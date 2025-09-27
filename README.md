# Apartment Availability Checker

Automated apartment availability checker for Irvine Company apartments with advanced web scraping, enhanced parsing, and live development environment.

## Features

- **Advanced Web Scraping**: Selenium-based scraping with Cloudflare bypass techniques
- **Enhanced Parsing**: Multiple parsing strategies to extract detailed apartment information
- **Live Development Environment**: File watching and automatic reloading for development
- **Anti-Detection**: Comprehensive browser fingerprinting prevention and stealth measures
- **Robust Fallbacks**: Multiple fallback strategies when primary methods fail
- **Detailed Data Extraction**: Extracts prices, floor plans, unit numbers, square footage, amenities, and more

## Key Components

### Main Scripts

- `apartment_checker_selenium.py` - Main apartment checker with Selenium web scraping
- `live_reload_simple.py` - Live reload development environment for iterative testing
- `apartment_checker.py` - Original apartment checker implementation
- `apartment_checker_curl.py` - cURL-based alternative implementation

### Development and Testing

- `test_*.py` - Various testing scripts for parsing logic validation
- `debug_features.py` - Feature extraction debugging utilities
- `show_apartment_parsing.py` - Apartment parsing result display utilities

## Installation

### Prerequisites

- Python 3.7+
- Chrome browser
- ChromeDriver (managed automatically by webdriver-manager)

### Dependencies

```bash
pip install selenium webdriver-manager requests beautifulsoup4 lxml
```

### Optional Dependencies

```bash
pip install python-dateutil  # For enhanced date parsing
```

## Usage

### Basic Usage

```bash
# Run once
python apartment_checker_selenium.py --debug

# Run continuously (checks every 30 minutes)
python apartment_checker_selenium.py --continuous

# Test parsing with mock data
python apartment_checker_selenium.py --test-parsing
```

### Development Workflow

For iterative development with live reload:

```bash
# Start live reload environment
python live_reload_simple.py --debug --script apartment_checker_selenium.py
```

This will:
- Monitor file changes
- Automatically re-run the script when changes are detected
- Display real-time parsing results
- Update `apartment_data.json` with latest results

## Configuration

### Environment Variables

- `CHROMEDRIVER_PATH` - Custom ChromeDriver path (optional)
- `APARTMENT_DATA_FILE` - Custom output file path (default: apartment_data.json)

### Browser Configuration

The script automatically configures Chrome with:
- Headless mode for background operation
- Enhanced stealth options to bypass detection
- Randomized user agents and browser properties
- Canvas fingerprinting protection
- WebRTC and plugin masking

## Data Output

Results are saved to `apartment_data.json` with the following structure:

```json
{
  "timestamp": "2024-01-01T12:00:00",
  "total_apartments": 19,
  "apartments": [
    {
      "unit": "01 561",
      "price": "$4,535",
      "floor_plan": "Plan 18",
      "bedrooms": 2,
      "bathrooms": 2,
      "square_feet": 1100,
      "status": "Available",
      "features": [
        "5th Floor",
        "Hardwood-Style Flooring",
        "Stainless Steel Appliances",
        "In-Home Washer/Dryer"
      ]
    }
  ]
}
```

## Architecture

### Parsing Strategies

The system uses multiple parsing strategies in order of preference:

1. **Structured Parsing** - Extracts data from well-formed HTML containers
2. **Table Parsing** - Handles table-based apartment listings
3. **JSON Parsing** - Extracts data from embedded JavaScript/JSON
4. **Fallback Parsing** - Price-based extraction as last resort

### Anti-Detection Measures

- Browser property masking (webdriver, plugins, languages)
- Canvas fingerprinting randomization
- Network connection simulation
- Battery API mocking
- Screen property normalization
- Random delays and human-like scrolling

### Error Handling

- Comprehensive fallback to requests-based scraping
- Network restriction detection and guidance
- Cloudflare challenge detection
- Automatic retry mechanisms
- Detailed error logging and debugging

## Development

### Live Reload Development

The project includes a sophisticated live reload system for rapid development:

```bash
python live_reload_simple.py --debug --script apartment_checker_selenium.py
```

Features:
- File change detection
- Automatic script reloading
- Real-time output monitoring
- Debug output management
- Error recovery

### Testing

Multiple testing approaches are available:

```bash
# Test with real website snapshot
python apartment_checker_selenium.py --test-parsing

# Test specific parsing components
python test_enhanced_parsing.py

# Debug feature extraction
python debug_features.py
```

## Troubleshooting

### Common Issues

**ChromeDriver Issues**
- The script automatically manages ChromeDriver installation
- For manual installation, ensure ChromeDriver matches your Chrome version

**Network Access Blocked (HTTP 403)**
- Try different networks (home WiFi, mobile hotspot)
- Disable VPN if active
- Check corporate firewall settings

**Cloudflare Challenges**
- The script includes comprehensive bypass techniques
- May require running from different IP addresses
- Consider using residential proxies for production use

**No Data Extracted**
- Use `--test-parsing` flag to test with saved website data
- Check if website structure has changed
- Review debug output in generated HTML files

### Debug Output

The script generates several debug files:
- `debug_content.html` - Full page content for analysis
- `apartment_snippet.html` - Content around apartment data
- `apartment_data.json` - Parsed results

## Contributing

This project uses an iterative development approach with live reload. To contribute:

1. Set up the live reload environment
2. Make incremental changes
3. Test with real website data using `--test-parsing`
4. Verify results in `apartment_data.json`
5. Submit pull requests with comprehensive testing

## Legal Notice

This tool is for educational and personal use only. Users are responsible for:
- Complying with website terms of service
- Respecting rate limits and server resources
- Following applicable laws and regulations
- Not using for commercial data harvesting

## License

This project is provided as-is for educational purposes. Please respect the target website's robots.txt and terms of service.