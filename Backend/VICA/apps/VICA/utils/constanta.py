from enum import Enum

class ERROR_MESSAGES(str, Enum):
    def __str__(self) -> str:
        return super().__str__()

    DEFAULT = lambda err="": f"Something went wrong :/\n{err if err else ''}"
    ENV_VAR_NOT_FOUND = "Required environment variable not found. Terminating now."
    CREATE_USER_ERROR = "Oops! Something went wrong while creating your account. Please try again later. If the issue persists, contact support for assistance."
    DELETE_USER_ERROR = "Oops! Something went wrong. We encountered an issue while trying to delete the user. Please give it another shot."
    EMAIL_MISMATCH = "Uh-oh! This email does not match the email your provider is registered with. Please check your email and try again."
    EMAIL_TAKEN = "Uh-oh! This email is already registered. Sign in with your existing account or choose another email to start anew."
    USERNAME_TAKEN = (
        "Uh-oh! This username is already registered. Please choose another username."
    )
    NAME_TAG_TAKEN = "Uh-oh! This name tag is already registered. Please choose another name tag string."
    INVALID_TOKEN = (
        "Your session has expired or the token is invalid. Please sign in again."
    )
    INVALID_CRED = "The email or password provided is incorrect. Please check for typos and try logging in again."
    INVALID_EMAIL_FORMAT = "The email format you entered is invalid. Please double-check and make sure you're using a valid email address (e.g., yourname@example.com)."
    INVALID_PASSWORD = (
        "The password provided is incorrect. Please check for typos and try again."
    )    
    UNAUTHORIZED = "401 Unauthorized"
    NOT_FOUND = "We could not find what you're looking for :/"
    USER_NOT_FOUND = "We could not find what you're looking for :/"
    ACCESS_PROHIBITED = "You do not have permission to access this resource. Please contact your administrator for assistance."
    ACTION_PROHIBITED = (
        "The requested action has been restricted as a security measure."
    )
    INVALID_TRUSTED_HEADER = "Your provider has not provided a trusted header. Please contact your administrator for assistance."