# Lockr Enterprise - Changelog

All notable changes to Lockr will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.91] - 2025-08-30

### Added
- **Systemd Service Integration**: Production-ready service management
  - Automatic startup on boot
  - Background operation without manual intervention
  - Professional service management with systemctl
- **Service Management Scripts**: 
  - `install_systemd_service.sh` for easy installation
  - `manage_lockr_service.sh` for comprehensive service control
- **Service Management Commands**: Easy control of Lockr service
  - `./manage_lockr_service.sh start|stop|restart|status|logs|info`
  - `./manage_lockr_service.sh enable|disable|install|uninstall`
- **Production Security Features**: Enterprise-grade service configuration
  - Restricted file system access
  - Resource limits and process controls
  - Secure service isolation
  - Journal logging integration

### Changed
- **Version Number**: Updated from 0.9 to 0.91
  - Major systemd integration upgrade
  - Production-ready service management

## [0.9] - 2025-08-30

### Added
- **Help System**: Comprehensive system overview and documentation
- **Versions Section**: System version tracking and release notes
- **Password Change Feature**: Admin password management with API endpoint
- **Enhanced Navigation**: Improved sidebar and section management

### Changed
- **Version Number**: Updated from 1.0.0 to 0.9
- **Button Labels**: More user-friendly terminology ("Add Account", "View Password")
- **Navigation Structure**: Cleaner dashboard organization

### Fixed
- **Navigation Issues**: Resolved section switching problems
- **Section Management**: Improved content visibility control

## [0.8] - 2025-08-30 (Previous Release)

### Added
- **Basic Server Management Dashboard**
- **Password Creation and Retrieval**
- **SSH Server Provisioning**
- **Light/Dark Theme Support**

### Core Features
- Enterprise server management dashboard
- Secure password generation and storage with Ansible Vault
- SSH-based server provisioning and management
- User validation and live password changes
- Professional web interface with light/dark themes
- Comprehensive audit logging and security

---

## Versioning Strategy

- **0.9**: Current development version
- **0.91, 0.92, etc.**: Incremental updates and bug fixes
- **1.0**: Production release for boss presentation
- **1.1, 1.2, etc.**: Post-production feature updates

## Notes

- Each version change is documented with detailed feature descriptions
- Technical improvements and bug fixes are tracked separately
- Security features are highlighted in each release
- Future versions will include migration guides and breaking changes
