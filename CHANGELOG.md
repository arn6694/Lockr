# Lockr Enterprise - Changelog

All notable changes to Lockr will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.95] - 2025-01-27

### Added
- **Targeted Health Check System**: Smart health check functionality that only checks degraded servers
- **Enhanced Health Check Modal**: Improved degraded servers modal with better error handling
- **New API Endpoint**: `/api/health_check_targeted` for checking specific servers only

### Technical Improvements
- **Optimized Health Check Performance**: Re-run health check now only processes degraded servers instead of all servers
- **Better Error Handling**: Fixed "Unexpected token '<'" error in health check details modal
- **Improved User Experience**: Loading messages now show exactly which servers are being checked
- **API Method Consistency**: Fixed GET vs POST method mismatch in health check endpoints

### Fixed
- **Health Check Modal Loading**: Fixed JavaScript errors when loading degraded server details
- **Re-run Health Check Button**: Now properly targets only degraded servers instead of all servers
- **Response Structure Mismatch**: Corrected API response property access in frontend code

## [0.94] - 2025-08-31

### Added
- **Comprehensive Health Check System**: Real-time server health monitoring
  - Connectivity testing (ping)
  - SSH port availability check
  - SSH key authentication verification
  - System resource monitoring (CPU, memory, disk)
- **Real Server Status Detection**: Accurate online/offline status instead of static counts
- **Health Check Dashboard**: Visual health status with detailed results modal
- **Enhanced Server Statistics**: Separate counts for online, offline, and degraded servers
- **Health Check API Endpoints**: `/api/health_check` and `/api/health_check_all`

### Technical Improvements
- **Server Status Validation**: Automatic connectivity testing on dashboard load
- **Health Check Results Modal**: Detailed breakdown of each health check component
- **Real-time Status Updates**: Server counts update based on actual connectivity
- **Enhanced Error Handling**: Comprehensive error reporting for health check failures

### Fixed
- **Server Count Accuracy**: Online servers count now reflects actual connectivity status
- **Status Icon Colors**: Online servers icon is now green, offline servers are red
- **Health Check Button**: Previously placeholder, now fully functional

## [0.93] - 2025-08-31

### Added
- **Timestamp Tracking System**: Implemented proper timestamp tracking for password operations
- **Last Updated Field**: Fixed the "Last updated" information to properly update when passwords are created, changed, or retrieved
- **Timestamp Files**: Added individual timestamp files for each password to track when they were last modified

### Technical Improvements
- **update_password_timestamp() Function**: New helper function to manage password timestamps
- **Enhanced Password Operations**: All password operations (create, change, retrieve) now update timestamps
- **Fallback Timestamp System**: Maintains backward compatibility with existing password files

## [0.92] - 2025-08-31

### Added
- **Ansible Playbook Integration**: Automated SSH setup via ser8 central server
- **ssh-copy-id Support**: Proper SSH key deployment workflow
- **Remote Setup Scripts**: `remote_setup.sh` for automated server configuration
- **Enhanced Logging**: Comprehensive Flask logging for debugging

### Fixed
- **Password Change Verification**: Root user password changes now work (SSH verification skipped)
- **SSH Setup Workflow**: Resolved Ansible playbook integration issues
- **Authentication Errors**: Fixed session management and authentication failures
- **Error Handling**: Enhanced debugging and logging for operations

### Technical Improvements
- **SSH Setup Automation**: Streamlined workflow for new server SSH configuration
- **Central Server Architecture**: ser8 (10.10.10.96) handles all SSH setup operations
- **Password Verification Logic**: Smart verification that works with server SSH configurations

### Latest Update (August 31, 2025 - 02:30)
- **Root Password Change Issue Resolved**: Fixed the "Failed to change password for user 'root'" error
- **SSH Verification Logic**: Identified that root SSH login is disabled on target servers
- **Smart Password Verification**: Modified verification to skip SSH testing for root users
- **Server Log Analysis**: Used server-side logs to diagnose the real issue
- **Password Management Now Fully Functional**: All user types (root and regular users) can have passwords changed successfully

---

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

- **0.9**: Previous development version
- **0.91**: Systemd service integration
- **0.92**: SSH setup and password management fixes
- **0.93**: Timestamp tracking system and Last Updated field fixes
- **0.94**: Current version - Comprehensive health check system and real server status detection
- **0.95, 0.96, etc.**: Incremental updates and bug fixes
- **1.0**: Production release for boss presentation
- **1.1, 1.2, etc.**: Post-production feature updates

## Notes

- Each version change is documented with detailed feature descriptions
- Technical improvements and bug fixes are tracked separately
- Security features are highlighted in each release
- Future versions will include migration guides and breaking changes

## 🗺️ Development Roadmap

### Immediate Priorities (v0.95)
- **Automatic Password Rotation**: Scheduled password changes with configurable intervals
- **API Tokens Panel**: Generate and manage scoped API tokens for third-party integration
- **Playbook Trigger Feedback**: Modal/toast confirmation with logs after playbook execution
- **Password Metadata**: Tags for "rotated," "expires in X days," "last used" lifecycle tracking
- **Password Length Enforcement**: Minimum character requirements with policy enforcement
  - **Frontend Validation**: Slider/input with minimum threshold (12+ characters)
  - **Policy Enforcement**: Global admin settings for minimum length enforcement
  - **Visual Feedback**: Dynamic strength meter and compliance indicators
  - **Default + Recommended**: 16 characters as recommended, 12 as minimum

### Short-term Goals (v0.96-0.97)
- **Audit Trail Panel**: Collapsible section showing recent vault access, playbook runs, and password changes
- **Search & Filter**: Fuzzy search and filters for server cards as inventory grows
- **Enhanced Password Lifecycle**: Expiration warnings and automatic rotation reminders
- **Advanced Playbook Management**: Playbook templates and execution history

### Long-term Vision (v1.0+)
- **Enterprise Features**: High availability, clustering, and advanced security
- **Compliance & Auditing**: SOC2, HIPAA, and industry-specific compliance features
- **Professional Support**: Enterprise support and documentation
- **Performance Optimization**: Advanced caching and connection pooling
