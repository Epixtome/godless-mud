# Godless MUD - V4.5 Cloud Container
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements if any
COPY requirements.txt .
RUN if [ -s requirements.txt ]; then pip install --no-cache-dir -r requirements.txt; fi

# Copy project files
COPY . .

# Ensure data directories exist (though .gitignore skips the content)
RUN mkdir -p data/saves data/live logs tmp

# Expose the Telnet port
EXPOSE 8888

# Command to run the MUD
CMD ["python", "godless_mud.py"]
