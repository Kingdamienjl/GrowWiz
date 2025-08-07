"""
GrowWiz Google Drive Manager
Handles Google Drive integration for organizing strain data
"""

import os
import json
import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
from loguru import logger
from care_sheet_generator import AdvancedCareSheetGenerator

# Import Athena's Google Drive operations
try:
    from mcp_athena import gdrive_operations
    GDRIVE_AVAILABLE = True
    logger.info("Google Drive operations available")
except ImportError:
    GDRIVE_AVAILABLE = False
    logger.warning("Google Drive operations not available")

class GDriveStrainManager:
    """Manages Google Drive folder structure and file uploads for strain data"""
    
    def __init__(self, base_folder_name: str = "GrowWiz_Strain_Database"):
        self.base_folder_name = base_folder_name
        self.base_folder_id = None
        self.strain_folders = {}  # strain_name -> folder_id mapping
        
        logger.info(f"GDriveStrainManager initialized with base folder: {base_folder_name}")
    
    async def setup_drive_structure(self) -> bool:
        """Set up the base Google Drive folder structure"""
        if not GDRIVE_AVAILABLE:
            logger.error("Google Drive operations not available")
            return False
        
        try:
            # Check authentication status
            auth_result = await gdrive_operations(operation="auth_status")
            if not auth_result.get('authenticated', False):
                logger.error("Google Drive not authenticated. Please authenticate first.")
                return False
            
            # Create base folder
            logger.info(f"Setting up Google Drive structure with base folder: {self.base_folder_name}")
            
            # Search for existing base folder
            search_result = await gdrive_operations(
                operation="search_files",
                query=f"name='{self.base_folder_name}' and mimeType='application/vnd.google-apps.folder'"
            )
            
            if search_result.get('files'):
                # Use existing folder
                self.base_folder_id = search_result['files'][0]['id']
                logger.info(f"Using existing base folder: {self.base_folder_id}")
            else:
                logger.info("Base folder will be created when first strain is uploaded")
            
            return True
            
        except Exception as e:
            logger.error(f"Error setting up Google Drive structure: {e}")
            return False
    
    async def create_strain_folder(self, strain_name: str) -> Optional[str]:
        """Create a folder for a specific strain"""
        if not GDRIVE_AVAILABLE:
            return None
        
        try:
            # Sanitize folder name
            safe_name = self._sanitize_folder_name(strain_name)
            
            # Check if folder already exists
            if safe_name in self.strain_folders:
                return self.strain_folders[safe_name]
            
            # Search for existing strain folder
            search_query = f"name='{safe_name}' and mimeType='application/vnd.google-apps.folder'"
            if self.base_folder_id:
                search_query += f" and '{self.base_folder_id}' in parents"
            
            search_result = await gdrive_operations(
                operation="search_files",
                query=search_query
            )
            
            if search_result.get('files'):
                # Use existing folder
                folder_id = search_result['files'][0]['id']
                self.strain_folders[safe_name] = folder_id
                logger.info(f"Using existing strain folder: {safe_name} ({folder_id})")
                return folder_id
            
            logger.info(f"Strain folder '{safe_name}' will be created when files are uploaded")
            return safe_name  # Return name as placeholder
            
        except Exception as e:
            logger.error(f"Error creating strain folder for {strain_name}: {e}")
            return None
    
    async def upload_strain_data(self, strain_data: Dict[str, Any], strain_folder_id: str) -> bool:
        """Upload strain data files to the strain's folder"""
        if not GDRIVE_AVAILABLE:
            logger.error("Google Drive not available for upload")
            return False
        
        try:
            strain_name = strain_data.get('name', 'Unknown')
            safe_name = self._sanitize_folder_name(strain_name)
            
            # Create local files for upload
            temp_dir = Path("temp_strain_data")
            temp_dir.mkdir(exist_ok=True)
            
            # Create strain info JSON
            info_file = temp_dir / f"{safe_name}_info.json"
            with open(info_file, 'w', encoding='utf-8') as f:
                json.dump(strain_data, f, indent=2, ensure_ascii=False)
            
            # Create strain summary text
            summary_file = temp_dir / f"{safe_name}_summary.txt"
            with open(summary_file, 'w', encoding='utf-8') as f:
                f.write(self._generate_strain_summary(strain_data))
            
            # Create growing guide
            guide_file = temp_dir / f"{safe_name}_growing_guide.md"
            with open(guide_file, 'w', encoding='utf-8') as f:
                f.write(self._generate_growing_guide(strain_data))
            
            logger.info(f"Created local files for {strain_name}, ready for Google Drive upload")
            
            # Attempt actual file upload using gdrive_operations
            try:
                # Upload info file
                info_result = await gdrive_operations(
                    operation="upload_file",
                    file_path=str(info_file),
                    parent_folder_id=strain_folder_id,
                    file_name=f"{safe_name}_info.json"
                )
                
                # Upload summary file
                summary_result = await gdrive_operations(
                    operation="upload_file",
                    file_path=str(summary_file),
                    parent_folder_id=strain_folder_id,
                    file_name=f"{safe_name}_summary.txt"
                )
                
                # Upload guide file
                guide_result = await gdrive_operations(
                    operation="upload_file",
                    file_path=str(guide_file),
                    parent_folder_id=strain_folder_id,
                    file_name=f"{safe_name}_growing_guide.md"
                )
                
                upload_success = (info_result.get('success', False) and 
                                summary_result.get('success', False) and 
                                guide_result.get('success', False))
                
                if upload_success:
                    logger.info(f"Successfully uploaded all files for {strain_name}")
                else:
                    logger.warning(f"Some files failed to upload for {strain_name}")
                    
            except Exception as upload_error:
                logger.error(f"Error during file upload: {upload_error}")
                upload_success = False
            
            # Clean up temp files
            for file in [info_file, summary_file, guide_file]:
                if file.exists():
                    file.unlink()
            
            if temp_dir.exists() and not any(temp_dir.iterdir()):
                temp_dir.rmdir()
            
            return upload_success
            
        except Exception as e:
            logger.error(f"Error uploading strain data: {e}")
            return False
    
    async def organize_strains_to_drive(self, strains_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Organize all strain data into Google Drive folders"""
        if not GDRIVE_AVAILABLE:
            return {"success": False, "error": "Google Drive not available"}
        
        results = {
            "success": True,
            "total_strains": len(strains_data),
            "uploaded_strains": 0,
            "failed_strains": 0,
            "strain_folders": {},
            "errors": []
        }
        
        try:
            # Setup base structure
            setup_success = await self.setup_drive_structure()
            if not setup_success:
                results["success"] = False
                results["errors"].append("Failed to setup Google Drive structure")
                return results
            
            logger.info(f"Starting to organize {len(strains_data)} strains to Google Drive")
            
            # Process each strain
            for i, strain_data in enumerate(strains_data, 1):
                try:
                    strain_name = strain_data.get('name', f'Unknown_Strain_{i}')
                    logger.info(f"Processing strain {i}/{len(strains_data)}: {strain_name}")
                    
                    # Create strain folder
                    folder_id = await self.create_strain_folder(strain_name)
                    if not folder_id:
                        results["failed_strains"] += 1
                        results["errors"].append(f"Failed to create folder for {strain_name}")
                        continue
                    
                    # Upload strain data
                    upload_success = await self.upload_strain_data(strain_data, folder_id)
                    if upload_success:
                        results["uploaded_strains"] += 1
                        results["strain_folders"][strain_name] = folder_id
                        logger.info(f"✅ Successfully organized {strain_name}")
                    else:
                        results["failed_strains"] += 1
                        results["errors"].append(f"Failed to upload data for {strain_name}")
                    
                    # Rate limiting
                    await asyncio.sleep(0.5)
                    
                except Exception as e:
                    results["failed_strains"] += 1
                    results["errors"].append(f"Error processing {strain_name}: {str(e)}")
                    logger.error(f"Error processing strain {strain_name}: {e}")
            
            # Final summary
            success_rate = (results["uploaded_strains"] / results["total_strains"]) * 100
            logger.info(f"Google Drive organization complete: {results['uploaded_strains']}/{results['total_strains']} strains ({success_rate:.1f}%)")
            
            return results
            
        except Exception as e:
            logger.error(f"Error organizing strains to Google Drive: {e}")
            results["success"] = False
            results["errors"].append(f"General error: {str(e)}")
            return results
    
    def _sanitize_folder_name(self, name: str) -> str:
        """Sanitize strain name for use as folder name"""
        # Remove invalid characters and limit length
        import re
        safe_name = re.sub(r'[<>:"/\\|?*]', '_', name)
        safe_name = safe_name.strip().replace(' ', '_')
        return safe_name[:50]  # Limit length
    
    def _generate_strain_summary(self, strain_data: Dict[str, Any]) -> str:
        """Generate a human-readable summary of strain data"""
        name = strain_data.get('name', 'Unknown')
        strain_type = strain_data.get('strain_type', 'Unknown')
        thc = strain_data.get('thc_content', 'Unknown')
        cbd = strain_data.get('cbd_content', 'Unknown')
        
        summary = f"""
🌿 {name} - Strain Summary
{'=' * 50}

Basic Information:
- Type: {strain_type.title()}
- THC Content: {thc}
- CBD Content: {cbd}
- Genetics: {strain_data.get('genetics', 'Unknown')}
- Breeder: {strain_data.get('breeder', 'Unknown')}

Growing Information:
- Flowering Time: {strain_data.get('flowering_time', 'Unknown')}
- Yield: {strain_data.get('yield_info', 'Unknown')}
- Difficulty: {strain_data.get('growing_difficulty', 'Unknown')}
- Height: {strain_data.get('height', 'Unknown')}
- Climate: {strain_data.get('climate', 'Unknown')}

Effects: {', '.join(strain_data.get('effects', []))}
Medical Uses: {', '.join(strain_data.get('medical_uses', []))}
Flavors: {', '.join(strain_data.get('flavors', []))}
Aromas: {', '.join(strain_data.get('aromas', []))}

Description:
{strain_data.get('description', 'No description available.')}

Awards: {', '.join(strain_data.get('awards', [])) or 'None listed'}

Data scraped on: {strain_data.get('scraped_at', 'Unknown')}
Source: {strain_data.get('source_url', 'Unknown')}
"""
        return summary
    
    def _generate_growing_guide(self, strain_data: Dict[str, Any]) -> str:
        """Generate a growing guide for the strain"""
        name = strain_data.get('name', 'Unknown')
        
        guide = f"""# {name} - Growing Guide

## Overview
- **Strain Type**: {strain_data.get('strain_type', 'Unknown').title()}
- **Difficulty**: {strain_data.get('growing_difficulty', 'Unknown')}
- **Flowering Time**: {strain_data.get('flowering_time', 'Unknown')}
- **Expected Yield**: {strain_data.get('yield_info', 'Unknown')}

## Plant Characteristics
- **Height**: {strain_data.get('height', 'Unknown')}
- **Climate Preference**: {strain_data.get('climate', 'Unknown')}
- **Genetics**: {strain_data.get('genetics', 'Unknown')}

## Growing Tips
Based on the strain type and characteristics:

### Lighting
- Provide 18-24 hours of light during vegetative stage
- Switch to 12/12 light cycle for flowering
- Use full-spectrum LED or HPS lights

### Nutrients
- Start with mild nutrient solution
- Increase gradually during flowering
- Monitor pH levels (6.0-7.0 for soil, 5.5-6.5 for hydro)

### Environment
- Temperature: 70-80°F (21-27°C) during day, 65-75°F (18-24°C) at night
- Humidity: 40-60% during vegetative, 40-50% during flowering
- Good air circulation is essential

### Harvesting
- Flowering time: {strain_data.get('flowering_time', 'Unknown')}
- Watch for trichome color change (clear to milky/amber)
- Harvest when 70-80% of trichomes are milky

## Expected Effects
{', '.join(strain_data.get('effects', []))}

## Medical Applications
{', '.join(strain_data.get('medical_uses', []))}

## Flavor Profile
- **Flavors**: {', '.join(strain_data.get('flavors', []))}
- **Aromas**: {', '.join(strain_data.get('aromas', []))}

---
*This guide is based on general strain characteristics. Always research specific growing requirements and local regulations.*
"""
        return guide
    
    async def get_drive_summary(self) -> Dict[str, Any]:
        """Get summary of Google Drive organization"""
        if not GDRIVE_AVAILABLE:
            return {"error": "Google Drive not available"}
        
        try:
            # Get folder information
            if self.base_folder_id:
                folder_info = await gdrive_operations(
                    operation="get_file_info",
                    fileId=self.base_folder_id
                )
                
                # List files in base folder
                files_result = await gdrive_operations(
                    operation="search_files",
                    query=f"'{self.base_folder_id}' in parents"
                )
                
                return {
                    "base_folder": folder_info,
                    "strain_folders_count": len(files_result.get('files', [])),
                    "strain_folders": self.strain_folders
                }
            else:
                return {
                    "base_folder": None,
                    "strain_folders_count": 0,
                    "strain_folders": {}
                }
                
        except Exception as e:
            logger.error(f"Error getting drive summary: {e}")
            return {"error": str(e)}

if __name__ == "__main__":
    async def main():
        manager = GDriveStrainManager()
        
        # Test setup
        success = await manager.setup_drive_structure()
        if success:
            print("✅ Google Drive structure setup successful")
            
            # Get summary
            summary = await manager.get_drive_summary()
            print(f"📊 Drive Summary: {summary}")
        else:
            print("❌ Failed to setup Google Drive structure")
    
    asyncio.run(main())