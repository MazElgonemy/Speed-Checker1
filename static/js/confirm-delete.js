function confirmDelete() {
    if (confirm("Are you sure you want to delete your account? This action cannot be undone.")) {
        // If confirmed, send a request to the server to delete the account
        window.location.href = "/delete-account";
    }
}
