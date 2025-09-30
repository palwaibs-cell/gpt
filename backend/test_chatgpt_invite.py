#!/usr/bin/env python3
import os
import sys
import logging
from dotenv import load_dotenv
from automation.chatgpt_inviter import ChatGPTTeamInviter

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_invitation(member_email, headless=False):
    """
    Test ChatGPT invitation manually

    Args:
        member_email (str): Email address to invite
        headless (bool): Run browser in headless mode (default: False for debugging)
    """
    try:
        logger.info(f"Testing ChatGPT invitation for: {member_email}")

        # Get credentials from environment
        admin_email = os.getenv('CHATGPT_ADMIN_EMAIL')
        admin_password = os.getenv('CHATGPT_ADMIN_PASSWORD')
        team_url = os.getenv('CHATGPT_ADMIN_URL', 'https://chatgpt.com/admin?tab=members')

        if not admin_email or not admin_password:
            logger.error("Missing admin credentials in environment variables")
            logger.error("Please set CHATGPT_ADMIN_EMAIL and CHATGPT_ADMIN_PASSWORD")
            return False

        logger.info(f"Using admin account: {admin_email}")
        logger.info(f"Team URL: {team_url}")
        logger.info(f"Headless mode: {headless}")

        # Create inviter instance
        inviter = ChatGPTTeamInviter(headless=headless, timeout=60)

        # Process invitation
        success = inviter.process_invitation(
            member_email=member_email,
            admin_email=admin_email,
            admin_password=admin_password,
            team_url=team_url
        )

        if success:
            logger.info(f"✓ Successfully invited {member_email}")
            return True
        else:
            logger.error(f"✗ Failed to invite {member_email}")
            return False

    except Exception as e:
        logger.error(f"Error during test: {str(e)}")
        return False

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python test_chatgpt_invite.py <email> [--headless]")
        print("\nExample:")
        print("  python test_chatgpt_invite.py test@example.com")
        print("  python test_chatgpt_invite.py test@example.com --headless")
        sys.exit(1)

    member_email = sys.argv[1]
    headless = '--headless' in sys.argv

    success = test_invitation(member_email, headless=headless)

    sys.exit(0 if success else 1)