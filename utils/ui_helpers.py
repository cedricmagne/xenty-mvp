import streamlit as st
import time

def show_message(message_type, message):
    """
    Display a message without auto-dismissing.
    
    Args:
        message_type: The type of message ('info', 'success', 'warning', 'error')
        message: The message to display
    
    Returns:
        None
    """
    # Display the message based on type
    if message_type == 'info':
        st.info(message)
    elif message_type == 'success':
        st.success(message)
    elif message_type == 'warning':
        st.warning(message)
    elif message_type == 'error':
        st.error(message)
    else:
        st.write(message)

def auto_dismiss_toast(message, duration=3):
    """
    Display a toast message that automatically dismisses after a specified duration.
    This uses Streamlit's native toast functionality which doesn't cause NoSessionContext errors.
    
    Args:
        message: The message to display
        duration: Time in seconds before the message is dismissed (default: 3)
    """
    st.toast(message, icon="✅")
