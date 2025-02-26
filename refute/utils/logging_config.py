from rich.logging import RichHandler
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,  # Change to DEBUG for more details
    format="%(message)s",
    datefmt="%H:%M:%S",
    handlers=[RichHandler()]
)


# Function to get a logger for each module
def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
