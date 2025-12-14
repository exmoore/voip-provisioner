"""Custom exception classes for the provisioner."""


class ProvisionerException(Exception):
    """Base exception for all provisioner errors."""

    pass


class PhoneNotFoundError(ProvisionerException):
    """Raised when a phone MAC address is not found in inventory."""

    pass


class DuplicateMACError(ProvisionerException):
    """Raised when attempting to add a phone with an existing MAC address."""

    pass


class DuplicateExtensionError(ProvisionerException):
    """Raised when attempting to use an extension that's already assigned."""

    pass


class InvalidMACError(ProvisionerException):
    """Raised when a MAC address format is invalid."""

    pass


class PersistenceError(ProvisionerException):
    """Raised when YAML file operations fail."""

    pass


class AsteriskError(ProvisionerException):
    """Raised when Asterisk AMI operations fail."""

    pass


class PhonebookEntryNotFoundError(ProvisionerException):
    """Raised when a phonebook entry is not found."""

    pass
