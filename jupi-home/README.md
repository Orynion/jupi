# JupiHome

Home Automation and AI Assistant Application built with C# and WPF.

## Overview

JupiHome is a Windows desktop application that combines home automation capabilities with AI-powered assistance. It provides a modern interface for controlling smart home devices and interacting with an intelligent assistant.

## Features

- Modern WPF-based user interface
- Home automation control system
- AI assistant integration
- Comprehensive logging system
- Dark theme optimized for usability

## Requirements

- .NET 8.0 or later
- Windows 10 or later
- Visual Studio 2022 or Visual Studio Code

## Project Structure

```
src/JupiHome/
├── App.xaml              # Application resources
├── App.xaml.cs           # Application entry point
├── MainWindow.xaml       # Main UI layout
├── MainWindow.xaml.cs    # Main window logic
├── Configuration/
│   └── AppSettings.cs    # Application configuration
├── Services/
│   └── Logger.cs         # Logging service
└── Properties/
    └── AssemblyInfo.cs   # Assembly metadata
```

## Getting Started

### Build

```bash
dotnet build
```

### Run

```bash
dotnet run
```

## Logging

The application automatically creates a logs directory and maintains daily log files. Logs are stored in `logs/jupihome_YYYY-MM-DD.log`.

## Configuration

Application settings can be modified in the `AppSettings.cs` file:

- `ApplicationName` - The display name of the application
- `Version` - Application version
- `EnableLogging` - Enable/disable logging
- `LogPath` - Directory for log files
- `Theme` - UI theme (dark/light)

## Development

This project uses:
- **WPF** for the user interface
- **Serilog** for structured logging
- **.NET 8.0** as the target framework

## License

Copyright © 2024 JupiHome. All rights reserved.
