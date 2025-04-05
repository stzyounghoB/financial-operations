import os
from datetime import datetime
from typing import List, Dict, Any, Optional, Union, Tuple, Type
import asyncio

from .interfaces.service_interface import ServiceInterface
from .service.ebs.volume.handler import VolumeHandler
from .service.ebs.snapshot.handler import SnapshotHandler
from .service.ami.handler import AMIHandler
from .service.dynamodb.cu.handler import DynamoCUHandler
from .output.output_factory import OutputFactory


class Menu:
    """AWS infrastructure checker menu interface"""
    
    # Region information
    REGIONS = {
        "1": "ap-northeast-1",
        "2": "ap-northeast-2",
        "3": "us-east-1",
        "4": "us-east-2",
        "5": "us-west-1",
        "6": "All regions"
    }
    
    # Output format information
    FORMATS = {
        "1": "json",
        "2": "csv",
        "3": "tsv",
        "4": "console"
    }
    
    # Main service menu
    MAIN_SERVICES = {
        "1": "EBS",
        "2": "AMI",
        "3": "DynamoDB",
        "4": "Exit"
    }
    
    # EBS sub-menu
    EBS_MENU = {
        "1": "Volumes",
        "2": "Snapshots",
        "3": "Back"
    }
    
    # EBS volume sub-menu
    VOLUME_MENU = {
        "1": "All volumes",
        "2": "Unused volumes",
        "3": "Back"
    }
    
    # AMI sub-menu
    AMI_MENU = {
        "1": "All AMIs",
        "2": "Unused AMIs",
        "3": "Back"
    }
    
    # DynamoDB sub-menu
    DYNAMODB_MENU = {
        "1": "CU usage (1 month)",
        "2": "CU usage (3 months)",
        "3": "CU usage (6 months)",
        "4": "Back"
    }
    
    def pick_aws_profile(self) -> Optional[Union[str, Tuple[str, str]]]:
        """
        Select AWS session information
        
        Returns:
            Optional[Union[str, Tuple[str, str]]]: Session information
        """
        print("\nAWS FinOps Program")
        print("Please select an AWS profile:")
        print("1. Default profile\n2. Named profile\n3. Key input")
        
        session_choice = input("Enter a number: ")
        
        if session_choice == "1":
            return None  # Use default profile
        elif session_choice == "2":
            profile_name = input("Enter AWS profile name: ")
            return profile_name if profile_name.strip() else None
        elif session_choice == "3":
            access_key = input("AWS Access Key: ")
            secret_key = input("AWS Secret Key: ")
            if access_key.strip() and secret_key.strip():
                return (access_key, secret_key)
            else:
                print("Invalid key information. Using default profile.")
                return None
        else:
            print("Invalid input. Using default profile.")
            return None
    
    def pick_region(self) -> List[str]:
        """
        Select AWS region(s) to use
        
        Returns:
            List[str]: Selected region list
        """
        print("\nPlease select a region:")
        for key, region in self.REGIONS.items():
            print(f"{key}. {region}")
        
        region_choice = input("Enter a number: ")
        
        if region_choice == "6":
            # Select all regions except "All regions"
            return list(value for key, value in self.REGIONS.items() if key != "6")
        elif region_choice in self.REGIONS:
            return [self.REGIONS[region_choice]]
        else:
            print("Invalid input. Using default region (ap-northeast-2).")
            return ["ap-northeast-2"]
    
    def pick_output_type(self) -> Tuple[Optional[str], str]:
        """
        Select output format and file path
        
        Returns:
            Tuple[Optional[str], str]: (file path, output format)
        """
        print("\nHow would you like to save the data?")
        for key, fmt in self.FORMATS.items():
            print(f"{key}. {fmt.upper()}")
        
        format_choice = input("Enter a number: ")
        format_type = self.FORMATS.get(format_choice, "console")
        
        file_path = None
        
        if format_type != "console":
            default_name = f"aws_infra_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{format_type}"
            directory = os.path.join(os.getcwd(), format_type)
            os.makedirs(directory, exist_ok=True)
            default_path = os.path.join(directory, default_name)
            
            file_path = input(f"\nEnter file path (default: {default_path}): ").strip()
            if not file_path:
                file_path = default_path
            
            # Check extension
            if not file_path.endswith(f".{format_type}"):
                file_path = f"{file_path}.{format_type}"
        
        return file_path, format_type
    
    async def main_menu(self, session: Optional[Union[str, tuple[str, str]]], regions: List[str]) -> None:
        """
        Display and handle main menu
        
        Args:
            session: AWS session information
            regions: Selected regions
        """
        while True:
            print("\nSelect an infrastructure service to check:")
            for key, service in self.MAIN_SERVICES.items():
                print(f"{key}. {service}")
            
            choice = input("Enter a number: ")
            
            if choice == "1":  # EBS
                await self.ebs_menu(session, regions)
            elif choice == "2":  # AMI
                await self.ami_menu(session, regions)
            elif choice == "3":  # DynamoDB
                await self.dynamodb_menu(session, regions)
            elif choice == "4":  # Exit
                print("Exiting program.")
                break
            else:
                print("Invalid choice. Please try again.")
    
    async def ebs_menu(self, session: Optional[Union[str, tuple[str, str]]], regions: List[str]) -> None:
        """
        Display and handle EBS menu
        
        Args:
            session: AWS session information
            regions: Selected regions
        """
        while True:
            print("\nEBS Services:")
            for key, option in self.EBS_MENU.items():
                print(f"{key}. {option}")
            
            choice = input("Enter a number: ")
            
            if choice == "1":  # Volumes
                await self.volume_menu(session, regions)
            elif choice == "2":  # Snapshots
                await self.handle_snapshots(session, regions)
            elif choice == "3":  # Back
                return
            else:
                print("Invalid choice. Please try again.")
    
    async def volume_menu(self, session: Optional[Union[str, tuple[str, str]]], regions: List[str]) -> None:
        """
        Display and handle volume menu
        
        Args:
            session: AWS session information
            regions: Selected regions
        """
        while True:
            print("\nEBS Volume Options:")
            for key, option in self.VOLUME_MENU.items():
                print(f"{key}. {option}")
            
            choice = input("Enter a number: ")
            
            if choice == "1":  # All volumes
                await self.handle_volumes(session, regions, False)
            elif choice == "2":  # Unused volumes
                await self.handle_volumes(session, regions, True)
            elif choice == "3":  # Back
                return
            else:
                print("Invalid choice. Please try again.")
    
    async def ami_menu(self, session: Optional[Union[str, tuple[str, str]]], regions: List[str]) -> None:
        """
        Display and handle AMI menu
        
        Args:
            session: AWS session information
            regions: Selected regions
        """
        while True:
            print("\nAMI Options:")
            for key, option in self.AMI_MENU.items():
                print(f"{key}. {option}")
            
            choice = input("Enter a number: ")
            
            if choice == "1":  # All AMIs
                await self.handle_amis(session, regions, False)
            elif choice == "2":  # Unused AMIs
                await self.handle_unused_amis(session, regions)
            elif choice == "3":  # Back
                return
            else:
                print("Invalid choice. Please try again.")
    
    async def dynamodb_menu(self, session: Optional[Union[str, tuple[str, str]]], regions: List[str]) -> None:
        """
        Display and handle DynamoDB menu
        
        Args:
            session: AWS session information
            regions: Selected regions
        """
        while True:
            print("\nDynamoDB Options:")
            for key, option in self.DYNAMODB_MENU.items():
                print(f"{key}. {option}")
            
            choice = input("Enter a number: ")
            
            if choice == "1":  # 1 month
                await self.handle_dynamo_cu(session, regions, 1)
            elif choice == "2":  # 3 months
                await self.handle_dynamo_cu(session, regions, 3)
            elif choice == "3":  # 6 months
                await self.handle_dynamo_cu(session, regions, 6)
            elif choice == "4":  # Back
                return
            else:
                print("Invalid choice. Please try again.")
    
    async def handle_volumes(self, session: Optional[Union[str, tuple[str, str]]], regions: List[str], unused_only: bool) -> None:
        """
        Handle EBS volume operations
        
        Args:
            session: AWS session information
            regions: Selected regions
            unused_only: Whether to show only unused volumes
        """
        print(f"\nFetching {'unused ' if unused_only else ''}EBS volumes from {len(regions)} region(s)...")
        results = []
        
        for region in regions:
            handler = VolumeHandler(region, session)
            if unused_only:
                volumes = await handler.fetch_unused_volumes()
            else:
                volumes = await handler.fetch_data()
            results.extend(volumes)
        
        if not results:
            print(f"No {'unused ' if unused_only else ''}EBS volumes found.")
            return
        
        # Output
        print(f"\nFound {len(results)} {'unused ' if unused_only else ''}EBS volumes.")
        file_path, format_type = self.pick_output_type()
        
        output_handler = OutputFactory.get_handler(format_type)
        await output_handler.output(results, file_path)
    
    async def handle_snapshots(self, session: Optional[Union[str, tuple[str, str]]], regions: List[str]) -> None:
        """
        Handle EBS snapshot operations
        
        Args:
            session: AWS session information
            regions: Selected regions
        """
        print(f"\nFetching EBS snapshots from {len(regions)} region(s)...")
        results = []
        
        for region in regions:
            handler = SnapshotHandler(region, session)
            snapshots = await handler.fetch_data()
            results.extend(snapshots)
        
        if not results:
            print("No EBS snapshots found.")
            return
        
        # Output
        print(f"\nFound {len(results)} EBS snapshots.")
        file_path, format_type = self.pick_output_type()
        
        output_handler = OutputFactory.get_handler(format_type)
        await output_handler.output(results, file_path)
    
    async def handle_amis(self, session: Optional[Union[str, tuple[str, str]]], regions: List[str], unused_only: bool) -> None:
        """
        Handle AMI operations
        
        Args:
            session: AWS session information
            regions: Selected regions
            unused_only: Whether to show only unused AMIs
        """
        print(f"\nFetching {'unused ' if unused_only else ''}AMIs from {len(regions)} region(s)...")
        results = []
        
        for region in regions:
            handler = AMIHandler(region, session)
            amis = await handler.fetch_data()
            results.extend(amis)
        
        if not results:
            print(f"No {'unused ' if unused_only else ''}AMIs found.")
            return
        
        # Output
        print(f"\nFound {len(results)} {'unused ' if unused_only else ''}AMIs.")
        file_path, format_type = self.pick_output_type()
        
        output_handler = OutputFactory.get_handler(format_type)
        await output_handler.output(results, file_path)
    
    async def handle_unused_amis(self, session: Optional[Union[str, tuple[str, str]]], regions: List[str]) -> None:
        """
        Handle unused AMI operations
        
        Args:
            session: AWS session information
            regions: Selected regions
        """
        print("\nFetching unused AMIs...")
        results = []
        
        # Fetch unused AMIs from each region
        for region in regions:
            handler = AMIHandler(region, session)
            unused_amis = await handler.fetch_unused_amis()
            results.extend(unused_amis)
        
        if not results:
            print("No unused AMIs found.")
            return
        
        # Display results
        print(f"\nFound {len(results)} unused AMIs:")
        for i, ami in enumerate(results, 1):
            print(f"{i}. ID: {ami['id']}, Name: {ami['name']}, Region: {ami['region']}, " +
                  f"Created: {ami['creation_date']}, Snapshots: {len(ami['snapshot_ids'])}")
        
        # Ask for action
        print("\nSelect an action:")
        print("1. Delete\n2. Output")
        action_choice = input("Enter a number: ").strip()
        
        if action_choice == "2":
            # Select output format
            file_path, format_type = self.pick_output_type()
            
            # Output results
            output_handler = OutputFactory.get_handler(format_type)
            await output_handler.output(results, file_path)
            return
        
        if action_choice != "1":
            print("Operation cancelled.")
            return
        
        # Select AMIs to delete
        selection = input("\nSelect AMI numbers to delete (comma-separated, 'all' for all): ").strip().lower()
        ami_to_delete = []
        
        if selection == 'all':
            ami_to_delete = [(ami['id'], ami['region']) for ami in results]
        else:
            try:
                indices = [int(idx.strip()) - 1 for idx in selection.split(',')]
                for idx in indices:
                    if 0 <= idx < len(results):
                        ami_to_delete.append((results[idx]['id'], results[idx]['region']))
                    else:
                        print(f"Invalid index: {idx + 1}")
            except ValueError:
                print("Invalid input.")
                return
        
        if not ami_to_delete:
            print("No AMIs selected.")
            return
        
        # Confirm snapshot deletion
        delete_snapshots = input("Delete associated snapshots too? (y/n): ").strip().lower() == 'y'
        
        # Group by region for deletion
        region_ami_map = {}
        for ami_id, region in ami_to_delete:
            if region not in region_ami_map:
                region_ami_map[region] = []
            region_ami_map[region].append(ami_id)
        
        # Delete AMIs in each region
        delete_results = []
        for region, ami_ids in region_ami_map.items():
            handler = AMIHandler(region, session)
            results = await handler.batch_delete_amis(ami_ids, delete_snapshots)
            delete_results.extend(results)
        
        # Display deletion results
        success_count = sum(1 for result in delete_results if result.get('success', False))
        print(f"\nAMI deletion complete: {success_count}/{len(delete_results)} successful")
        
        for result in delete_results:
            if result.get('success', False):
                print(f"Success: {result.get('message', '')}")
            else:
                print(f"Failed: {result.get('message', '')}")
    
    async def handle_dynamo_cu(self, session: Optional[Union[str, tuple[str, str]]], regions: List[str], months: int) -> None:
        """
        Handle DynamoDB CU operations
        
        Args:
            session: AWS session information
            regions: Selected regions
            months: Number of months for metrics
        """
        print(f"\nAnalyzing DynamoDB CU usage ({months} months)...")
        results = []
        
        # Fetch DynamoDB tables from each region
        for region in regions:
            handler = DynamoCUHandler(region, session, months)
            table_metrics = await handler.fetch_data()
            results.extend(table_metrics)
        
        if not results:
            print("No DynamoDB tables to analyze.")
            return
        
        # Display summary
        print(f"\nAnalyzed {len(results)} DynamoDB tables:")
        print(f"Period: Last {months} month(s)")
        
        # Find low utilization tables (below 20%)
        low_utilization = [t for t in results if t["billing_mode"] == "PROVISIONED" and 
                           (t["wcu_utilization_percent"] < 20 or t["rcu_utilization_percent"] < 20)]
        
        if low_utilization:
            print(f"\nLow utilization tables ({len(low_utilization)}):")
            for table in low_utilization:
                print(f"  - {table['table_name']} (Region: {table['region']})")
                print(f"    WCU utilization: {table['wcu_utilization_percent']}%, RCU utilization: {table['rcu_utilization_percent']}%")
        
        # Select output format
        file_path, format_type = self.pick_output_type()
        
        # Output results
        output_handler = OutputFactory.get_handler(format_type)
        await output_handler.output(results, file_path)