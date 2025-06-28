import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import re
from pypdf import PdfReader
import schedule
import time
import threading
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class InsuranceReminder:
    def __init__(self):
        """Initialize the insurance reminder system"""
        self.policies = {}  # Dictionary to store policy information
        self.notification_callback = None
        self.running = False
        self.thread = None

    def extract_due_date(self, text: str) -> Optional[datetime]:
        """Extract due date from text using various patterns"""
        # Common date patterns in insurance documents
        date_patterns = [
            r'due date[:\s]+(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
            r'due date[:\s]+([A-Za-z]+ \d{1,2}, \d{4})',
            r'premium due[:\s]+(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
            r'premium due[:\s]+([A-Za-z]+ \d{1,2}, \d{4})',
            r'payment due[:\s]+(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
            r'payment due[:\s]+([A-Za-z]+ \d{1,2}, \d{4})',
            r'next payment[:\s]+(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
            r'next payment[:\s]+([A-Za-z]+ \d{1,2}, \d{4})',
            r'premium date[:\s]+(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
            r'premium date[:\s]+([A-Za-z]+ \d{1,2}, \d{4})',
            # Add flexible pattern for Next Due
            r'next\s*due[:\s]+(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
            r'next\s*due[:\s]+([A-Za-z]+ \d{1,2}, \d{4})',
        ]

        for pattern in date_patterns:
            match = re.search(pattern, text.lower())
            if match:
                date_str = match.group(1)
                try:
                    # Try different date formats
                    for fmt in ['%d/%m/%Y', '%d-%m-%Y', '%d/%m/%y', '%d-%m-%y', '%B %d, %Y']:
                        try:
                            return datetime.strptime(date_str, fmt)
                        except ValueError:
                            continue
                except Exception as e:
                    logger.error(f"Error parsing date {date_str}: {str(e)}")
                    continue

        return None

    def process_policy_pdf(self, file_path: str) -> bool:
        """Process a policy PDF and extract due date information"""
        try:
            # Read PDF file
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"

            # Extract due date
            due_date = self.extract_due_date(text)
            if not due_date:
                logger.warning(f"Could not find due date in {file_path}")
                return False

            # Store policy information
            policy_info = {
                'file_path': file_path,
                'due_date': due_date,
                'last_checked': datetime.now(),
                'notified': False
            }
            
            self.policies[file_path] = policy_info
            logger.info(f"Processed policy {file_path} with due date {due_date}")
            return True

        except Exception as e:
            logger.error(f"Error processing policy PDF {file_path}: {str(e)}")
            return False

    def check_upcoming_payments(self):
        """Check for upcoming payments and trigger notifications"""
        current_date = datetime.now()
        one_week_from_now = current_date + timedelta(days=7)

        for file_path, policy in self.policies.items():
            if policy['notified']:
                continue

            due_date = policy['due_date']
            if current_date <= due_date <= one_week_from_now:
                # Trigger notification
                if self.notification_callback:
                    self.notification_callback(
                        file_path=file_path,
                        due_date=due_date,
                        days_remaining=(due_date - current_date).days
                    )
                policy['notified'] = True
                policy['last_checked'] = current_date
                logger.info(f"Notification sent for policy {file_path}")

    def set_notification_callback(self, callback):
        """Set the callback function for notifications"""
        self.notification_callback = callback

    def start_monitoring(self):
        """Start the monitoring thread"""
        if self.running:
            return

        self.running = True
        self.thread = threading.Thread(target=self._monitor_loop)
        self.thread.daemon = True
        self.thread.start()

    def stop_monitoring(self):
        """Stop the monitoring thread"""
        self.running = False
        if self.thread:
            self.thread.join()

    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.running:
            try:
                self.check_upcoming_payments()
                time.sleep(3600)  # Check every hour
            except Exception as e:
                logger.error(f"Error in monitoring loop: {str(e)}")
                time.sleep(300)  # Wait 5 minutes before retrying

    def get_policy_info(self, file_path: str) -> Optional[Dict]:
        """Get information about a specific policy"""
        return self.policies.get(file_path)

    def get_all_policies(self) -> List[Dict]:
        """Get information about all policies"""
        return list(self.policies.values())

    def remove_policy(self, file_path: str) -> bool:
        """Remove a policy from monitoring"""
        if file_path in self.policies:
            del self.policies[file_path]
            return True
        return False 