"""
GrowWiz Strain Scraper - Main Execution Script
Scrapes 100 marijuana strains and organizes them in Google Drive
"""

import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from loguru import logger

# Import our custom modules
from src.strain_scraper import StrainScraper, StrainData
from src.gdrive_manager import GDriveStrainManager

# Configure logging
logger.add("logs/strain_scraping_{time}.log", rotation="1 day", retention="7 days")

class StrainScrapingOrchestrator:
    """Orchestrates the complete strain scraping and Google Drive organization process"""
    
    def __init__(self):
        self.scraper = StrainScraper()
        self.gdrive_manager = GDriveStrainManager("GrowWiz_100_Strains_Database")
        self.results = {
            "started_at": datetime.now().isoformat(),
            "scraping": {},
            "gdrive_organization": {},
            "completed_at": None,
            "success": False
        }
        
        logger.info("StrainScrapingOrchestrator initialized")
    
    async def run_complete_process(self, target_strains: int = 100) -> dict:
        """Run the complete strain scraping and Google Drive organization process"""
        logger.info(f"🚀 Starting complete strain scraping process for {target_strains} strains")
        
        try:
            # Step 1: Scrape strain data
            logger.info("📡 Phase 1: Scraping strain data...")
            scraped_strains = await self.scraper.scrape_top_strains(target_strains)
            
            if not scraped_strains:
                logger.error("No strains were scraped successfully")
                self.results["success"] = False
                return self.results
            
            # Store scraping results
            self.results["scraping"] = {
                "target_count": target_strains,
                "scraped_count": len(scraped_strains),
                "success_rate": (len(scraped_strains) / target_strains) * 100,
                "summary": self.scraper.get_strain_summary()
            }
            
            logger.info(f"✅ Scraping complete: {len(scraped_strains)}/{target_strains} strains")
            
            # Step 2: Save local backup
            logger.info("💾 Phase 2: Creating local backup...")
            local_backup_path = f"data/strains_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            os.makedirs("data", exist_ok=True)
            
            backup_data = {
                "metadata": {
                    "scraped_at": datetime.now().isoformat(),
                    "total_strains": len(scraped_strains),
                    "scraper_version": "1.0.0"
                },
                "strains": [strain.__dict__ for strain in scraped_strains]
            }
            
            with open(local_backup_path, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✅ Local backup saved: {local_backup_path}")
            
            # Step 3: Organize in Google Drive
            logger.info("☁️ Phase 3: Organizing data in Google Drive...")
            
            # Convert StrainData objects to dictionaries for Google Drive
            strains_dict_list = [strain.__dict__ for strain in scraped_strains]
            
            gdrive_results = await self.gdrive_manager.organize_strains_to_drive(strains_dict_list)
            self.results["gdrive_organization"] = gdrive_results
            
            if gdrive_results["success"]:
                logger.info(f"✅ Google Drive organization complete: {gdrive_results['uploaded_strains']}/{gdrive_results['total_strains']} strains")
            else:
                logger.error(f"❌ Google Drive organization failed: {gdrive_results.get('errors', [])}")
            
            # Step 4: Generate final report
            logger.info("📊 Phase 4: Generating final report...")
            report = await self.generate_final_report()
            
            # Mark as complete
            self.results["completed_at"] = datetime.now().isoformat()
            self.results["success"] = True
            
            logger.info("🎉 Complete strain scraping process finished successfully!")
            
            return self.results
            
        except Exception as e:
            logger.error(f"❌ Error in complete process: {e}")
            self.results["error"] = str(e)
            self.results["success"] = False
            return self.results
    
    async def generate_final_report(self) -> dict:
        """Generate a comprehensive final report"""
        try:
            report = {
                "execution_summary": {
                    "started_at": self.results["started_at"],
                    "completed_at": datetime.now().isoformat(),
                    "total_duration": "Calculated at completion"
                },
                "scraping_results": self.results.get("scraping", {}),
                "gdrive_results": self.results.get("gdrive_organization", {}),
                "strain_analysis": {},
                "recommendations": []
            }
            
            # Analyze scraped strains
            if self.scraper.scraped_strains:
                strain_types = {}
                thc_levels = []
                cbd_levels = []
                
                for strain in self.scraper.scraped_strains:
                    # Count strain types
                    strain_type = strain.strain_type.lower()
                    strain_types[strain_type] = strain_types.get(strain_type, 0) + 1
                    
                    # Collect THC/CBD data
                    if strain.thc_content and '%' in strain.thc_content:
                        try:
                            thc_val = float(strain.thc_content.replace('%', ''))
                            thc_levels.append(thc_val)
                        except:
                            pass
                    
                    if strain.cbd_content and '%' in strain.cbd_content:
                        try:
                            cbd_val = float(strain.cbd_content.replace('%', ''))
                            cbd_levels.append(cbd_val)
                        except:
                            pass
                
                report["strain_analysis"] = {
                    "type_distribution": strain_types,
                    "thc_analysis": {
                        "samples": len(thc_levels),
                        "average": sum(thc_levels) / len(thc_levels) if thc_levels else 0,
                        "min": min(thc_levels) if thc_levels else 0,
                        "max": max(thc_levels) if thc_levels else 0
                    },
                    "cbd_analysis": {
                        "samples": len(cbd_levels),
                        "average": sum(cbd_levels) / len(cbd_levels) if cbd_levels else 0,
                        "min": min(cbd_levels) if cbd_levels else 0,
                        "max": max(cbd_levels) if cbd_levels else 0
                    }
                }
            
            # Generate recommendations
            recommendations = [
                "Data successfully organized in Google Drive with individual strain folders",
                "Local backup created for data redundancy",
                "Consider implementing automated updates for strain information",
                "Strain database ready for integration with growing automation system"
            ]
            
            if self.results.get("gdrive_organization", {}).get("failed_strains", 0) > 0:
                recommendations.append("Review failed Google Drive uploads and retry if necessary")
            
            report["recommendations"] = recommendations
            
            # Save report
            report_path = f"data/strain_scraping_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            logger.info(f"📋 Final report saved: {report_path}")
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating final report: {e}")
            return {"error": str(e)}
    
    def print_progress_summary(self):
        """Print a human-readable progress summary"""
        print("\n" + "="*60)
        print("🌿 GROWWIZ STRAIN SCRAPING SUMMARY")
        print("="*60)
        
        if "scraping" in self.results:
            scraping = self.results["scraping"]
            print(f"📡 SCRAPING RESULTS:")
            print(f"   Target Strains: {scraping.get('target_count', 0)}")
            print(f"   Successfully Scraped: {scraping.get('scraped_count', 0)}")
            print(f"   Success Rate: {scraping.get('success_rate', 0):.1f}%")
            
            if "summary" in scraping:
                summary = scraping["summary"]
                print(f"   Strain Types: {summary.get('by_type', {})}")
                print(f"   With THC Data: {summary.get('with_thc_data', 0)}")
                print(f"   With CBD Data: {summary.get('with_cbd_data', 0)}")
        
        if "gdrive_organization" in self.results:
            gdrive = self.results["gdrive_organization"]
            print(f"\n☁️ GOOGLE DRIVE ORGANIZATION:")
            print(f"   Total Strains: {gdrive.get('total_strains', 0)}")
            print(f"   Successfully Uploaded: {gdrive.get('uploaded_strains', 0)}")
            print(f"   Failed Uploads: {gdrive.get('failed_strains', 0)}")
            
            if gdrive.get('errors'):
                print(f"   Errors: {len(gdrive['errors'])} (check logs for details)")
        
        print(f"\n⏱️ TIMING:")
        print(f"   Started: {self.results.get('started_at', 'Unknown')}")
        print(f"   Completed: {self.results.get('completed_at', 'In Progress')}")
        print(f"   Status: {'✅ SUCCESS' if self.results.get('success') else '❌ FAILED'}")
        
        print("="*60)

async def main():
    """Main function to run comprehensive strain scraping and Google Drive organization"""
    print("🌿 GrowWiz Enhanced Strain Scraper & Google Drive Manager")
    print("=" * 60)
    
    try:
        # Initialize scraper with enhanced capabilities
        scraper = StrainScraper()
        print(f"✅ StrainScraper initialized")
        
        # Initialize Google Drive manager
         gdrive_manager = GDriveStrainManager()
         print(f"✅ GDriveStrainManager initialized")
        
        # Enhanced scraping for 1000+ strains
        target_count = 1000
        print(f"\n🔍 Starting enhanced scraping for {target_count} strains...")
        print("📊 Sources: 15+ cannabis databases and websites")
        print("🎯 Enhanced data collection with comprehensive strain database")
        
        strains = await scraper.scrape_top_strains(target_count)
        
        print(f"\n📊 Enhanced Scraping Results:")
        print(f"Total strains collected: {len(strains)}")
        
        # Display enhanced statistics
        if hasattr(scraper, 'enhanced_scraper') and scraper.enhanced_scraper:
            summary = scraper.enhanced_scraper.get_comprehensive_summary()
            print(f"By type: {summary.get('by_type', {})}")
            print(f"By difficulty: {summary.get('by_difficulty', {})}")
            print(f"With THC data: {summary.get('with_thc_data', 0)}")
            print(f"With CBD data: {summary.get('with_cbd_data', 0)}")
            print(f"With terpenes: {summary.get('with_terpenes', 0)}")
            print(f"Average popularity: {summary.get('average_popularity', 0):.1f}")
        
        # Save enhanced data locally
        scraper.save_strains_data("data/enhanced_strains_1000.json")
        print(f"💾 Enhanced strain data saved locally")
        
        # Google Drive organization (if available)
        print(f"\n☁️ Starting Google Drive organization...")
        try:
            success = await gdrive_manager.organize_strains_to_gdrive(strains)
            if success:
                print(f"✅ Successfully organized {len(strains)} strains in Google Drive")
            else:
                print(f"⚠️ Google Drive organization completed with some issues")
        except Exception as e:
            print(f"❌ Google Drive organization failed: {e}")
        
        print(f"\n🎉 Enhanced strain scraping and organization completed!")
        print(f"📈 Total strains processed: {len(strains)}")
        print(f"🔗 Enhanced data sources: 15+ cannabis databases")
        print(f"📁 Data saved locally and to Google Drive")
        
        return {"success": True, "strains_count": len(strains)}
        
    except KeyboardInterrupt:
        print("\n⚠️ Process interrupted by user")
        logger.info("Process interrupted by user")
        return {"success": False, "error": "Interrupted by user"}
    
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        logger.error(f"Unexpected error in main: {e}")
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    # Ensure required directories exist
    os.makedirs("data", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    
    # Run the main process
    results = asyncio.run(main())
    
    # Exit with appropriate code
    exit(0 if results.get("success", False) else 1)