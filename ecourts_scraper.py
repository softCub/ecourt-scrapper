#!/usr/bin/env python3
"""
eCourts India Case Listing Scraper
Fetches court listings and case details from eCourts India portal
"""

import requests
import json
import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import time
import re


class ECourtsScraper:
    """Scraper for eCourts India portal"""
    
    BASE_URL = "https://services.ecourts.gov.in/ecourtindia_v6"
    
    def __init__(self, state_code: str = "DL", district_code: str = "1"):
        """
        Initialize scraper with state and district codes
        
        Args:
            state_code: State code (default: DL for Delhi)
            district_code: District code (default: 1)
        """
        self.state_code = state_code
        self.district_code = district_code
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': f'{self.BASE_URL}/'
        })
        
    def _make_request(self, endpoint: str, method: str = "GET", 
                     data: Optional[Dict] = None, params: Optional[Dict] = None) -> Optional[requests.Response]:
        """Make HTTP request with error handling"""
        try:
            url = f"{self.BASE_URL}/{endpoint}"
            if method == "GET":
                response = self.session.get(url, params=params, timeout=30)
            else:
                response = self.session.post(url, data=data, params=params, timeout=30)
            
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            print(f"❌ Request error: {e}", file=sys.stderr)
            return None
    
    def get_case_by_cnr(self, cnr: str) -> Optional[Dict]:
        """
        Fetch case details by CNR number
        
        Args:
            cnr: CNR (Case Number Registry) number
            
        Returns:
            Dictionary with case details or None
        """
        print(f"🔍 Searching for CNR: {cnr}")
        
        # In real implementation, would make API call to eCourts
        # This is a template showing the structure
        endpoint = "case_status/cnr_search.php"
        data = {
            'state_code': self.state_code,
            'dist_code': self.district_code,
            'cnr_number': cnr
        }
        
        response = self._make_request(endpoint, "POST", data=data)
        if response:
            try:
                return response.json()
            except json.JSONDecodeError:
                print("❌ Failed to parse response", file=sys.stderr)
        return None
    
    def get_case_by_details(self, case_type: str, case_number: str, 
                           case_year: str) -> Optional[Dict]:
        """
        Fetch case details by case type, number, and year
        
        Args:
            case_type: Type of case (e.g., CS, CRL, etc.)
            case_number: Case number
            case_year: Year of case filing
            
        Returns:
            Dictionary with case details or None
        """
        print(f"🔍 Searching for case: {case_type}/{case_number}/{case_year}")
        
        endpoint = "case_status/case_number_search.php"
        data = {
            'state_code': self.state_code,
            'dist_code': self.district_code,
            'case_type': case_type,
            'case_no': case_number,
            'case_year': case_year
        }
        
        response = self._make_request(endpoint, "POST", data=data)
        if response:
            try:
                return response.json()
            except json.JSONDecodeError:
                print("❌ Failed to parse response", file=sys.stderr)
        return None
    
    def check_listing(self, case_details: Dict, date: datetime) -> Optional[Dict]:
        """
        Check if case is listed on given date
        
        Args:
            case_details: Case information dictionary
            date: Date to check listing for
            
        Returns:
            Dictionary with listing info (serial number, court name) or None
        """
        date_str = date.strftime("%d-%m-%Y")
        print(f"📅 Checking listing for {date_str}")
        
        # Template for API call to check cause list
        endpoint = "cause_list/listing_by_date.php"
        data = {
            'state_code': self.state_code,
            'dist_code': self.district_code,
            'date': date_str,
            'case_id': case_details.get('case_id', '')
        }
        
        response = self._make_request(endpoint, "POST", data=data)
        if response:
            try:
                listing = response.json()
                if listing.get('is_listed'):
                    return {
                        'date': date_str,
                        'serial_number': listing.get('serial_no'),
                        'court_name': listing.get('court_name'),
                        'court_hall': listing.get('court_hall'),
                        'hearing_time': listing.get('hearing_time')
                    }
            except json.JSONDecodeError:
                pass
        return None
    
    def download_case_pdf(self, case_details: Dict, output_dir: str = "downloads") -> Optional[str]:
        """
        Download case PDF if available
        
        Args:
            case_details: Case information dictionary
            output_dir: Directory to save PDF
            
        Returns:
            Path to downloaded file or None
        """
        print("📄 Attempting to download case PDF...")
        
        Path(output_dir).mkdir(exist_ok=True)
        
        endpoint = "case_status/download_case_pdf.php"
        params = {
            'case_id': case_details.get('case_id', ''),
            'state_code': self.state_code
        }
        
        response = self._make_request(endpoint, "GET", params=params)
        if response and response.headers.get('content-type') == 'application/pdf':
            filename = f"{output_dir}/case_{case_details.get('cnr', 'unknown')}.pdf"
            with open(filename, 'wb') as f:
                f.write(response.content)
            print(f"✅ PDF saved: {filename}")
            return filename
        
        print("❌ PDF not available", file=sys.stderr)
        return None
    
    def download_cause_list(self, date: datetime, output_dir: str = "downloads") -> Optional[str]:
        """
        Download entire cause list for given date
        
        Args:
            date: Date for cause list
            output_dir: Directory to save files
            
        Returns:
            Path to saved JSON file or None
        """
        date_str = date.strftime("%d-%m-%Y")
        print(f"📋 Downloading cause list for {date_str}...")
        
        Path(output_dir).mkdir(exist_ok=True)
        
        endpoint = "cause_list/daily_cause_list.php"
        data = {
            'state_code': self.state_code,
            'dist_code': self.district_code,
            'date': date_str
        }
        
        response = self._make_request(endpoint, "POST", data=data)
        if response:
            try:
                cause_list = response.json()
                filename = f"{output_dir}/cause_list_{date.strftime('%Y%m%d')}.json"
                
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(cause_list, f, indent=2, ensure_ascii=False)
                
                print(f"✅ Cause list saved: {filename}")
                return filename
            except json.JSONDecodeError:
                print("❌ Failed to parse cause list", file=sys.stderr)
        
        return None
    
    def save_results(self, data: Dict, filename: str, output_dir: str = "output"):
        """Save results to JSON file"""
        Path(output_dir).mkdir(exist_ok=True)
        filepath = f"{output_dir}/{filename}"
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Results saved: {filepath}")
        return filepath


def display_case_info(case_details: Dict, listing_info: Optional[Dict] = None):
    """Display case information in formatted manner"""
    print("\n" + "="*60)
    print("📋 CASE INFORMATION")
    print("="*60)
    
    if case_details:
        print(f"CNR Number: {case_details.get('cnr', 'N/A')}")
        print(f"Case Type: {case_details.get('case_type', 'N/A')}")
        print(f"Case Number: {case_details.get('case_number', 'N/A')}")
        print(f"Filing Year: {case_details.get('filing_year', 'N/A')}")
        print(f"Petitioner: {case_details.get('petitioner_name', 'N/A')}")
        print(f"Respondent: {case_details.get('respondent_name', 'N/A')}")
    
    if listing_info:
        print("\n" + "-"*60)
        print("📅 LISTING DETAILS")
        print("-"*60)
        print(f"✅ Case is LISTED on {listing_info['date']}")
        print(f"Serial Number: {listing_info.get('serial_number', 'N/A')}")
        print(f"Court Name: {listing_info.get('court_name', 'N/A')}")
        print(f"Court Hall: {listing_info.get('court_hall', 'N/A')}")
        print(f"Hearing Time: {listing_info.get('hearing_time', 'N/A')}")
    else:
        print("\n❌ Case is NOT listed for the specified date(s)")
    
    print("="*60 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description='eCourts India Case Listing Scraper',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --cnr DLNC01234567890
  %(prog)s --case-type CS --case-number 123 --case-year 2024
  %(prog)s --cnr DLNC01234567890 --today --tomorrow
  %(prog)s --causelist --today
  %(prog)s --cnr DLNC01234567890 --download-pdf
        """
    )
    
    # Case search options
    search_group = parser.add_argument_group('Case Search')
    search_group.add_argument('--cnr', help='CNR (Case Number Registry) number')
    search_group.add_argument('--case-type', help='Case type (e.g., CS, CRL)')
    search_group.add_argument('--case-number', help='Case number')
    search_group.add_argument('--case-year', help='Case filing year')
    
    # Listing check options
    listing_group = parser.add_argument_group('Listing Check')
    listing_group.add_argument('--today', action='store_true', 
                              help='Check if case is listed today')
    listing_group.add_argument('--tomorrow', action='store_true',
                              help='Check if case is listed tomorrow')
    
    # Download options
    download_group = parser.add_argument_group('Download Options')
    download_group.add_argument('--download-pdf', action='store_true',
                               help='Download case PDF if available')
    download_group.add_argument('--causelist', action='store_true',
                               help='Download entire cause list')
    
    # Configuration
    config_group = parser.add_argument_group('Configuration')
    config_group.add_argument('--state', default='DL', help='State code (default: DL)')
    config_group.add_argument('--district', default='1', help='District code (default: 1)')
    config_group.add_argument('--output-dir', default='output', help='Output directory')
    
    args = parser.parse_args()
    
    # Validate inputs
    if not args.cnr and not (args.case_type and args.case_number and args.case_year) and not args.causelist:
        parser.error("Provide either --cnr OR (--case-type, --case-number, --case-year) OR --causelist")
    
    if args.causelist and not (args.today or args.tomorrow):
        parser.error("--causelist requires --today or --tomorrow")
    
    # Initialize scraper
    scraper = ECourtsScraper(state_code=args.state, district_code=args.district)
    
    # Download cause list if requested
    if args.causelist:
        dates = []
        if args.today:
            dates.append(datetime.now())
        if args.tomorrow:
            dates.append(datetime.now() + timedelta(days=1))
        
        for date in dates:
            scraper.download_cause_list(date, output_dir=args.output_dir)
        
        if not args.cnr and not args.case_type:
            return
    
    # Fetch case details
    case_details = None
    if args.cnr:
        case_details = scraper.get_case_by_cnr(args.cnr)
    elif args.case_type and args.case_number and args.case_year:
        case_details = scraper.get_case_by_details(
            args.case_type, args.case_number, args.case_year
        )
    
    if not case_details:
        print("❌ Could not fetch case details", file=sys.stderr)
        sys.exit(1)
    
    # Check listings
    listing_info = None
    if args.today or args.tomorrow:
        dates = []
        if args.today:
            dates.append(('today', datetime.now()))
        if args.tomorrow:
            dates.append(('tomorrow', datetime.now() + timedelta(days=1)))
        
        for label, date in dates:
            info = scraper.check_listing(case_details, date)
            if info:
                listing_info = info
                break
    
    # Display results
    display_case_info(case_details, listing_info)
    
    # Download PDF if requested
    if args.download_pdf:
        scraper.download_case_pdf(case_details, output_dir=args.output_dir)
    
    # Save results
    results = {
        'timestamp': datetime.now().isoformat(),
        'case_details': case_details,
        'listing_info': listing_info,
        'search_params': {
            'cnr': args.cnr,
            'case_type': args.case_type,
            'case_number': args.case_number,
            'case_year': args.case_year
        }
    }
    
    filename = f"case_search_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    scraper.save_results(results, filename, output_dir=args.output_dir)


if __name__ == "__main__":
    main()