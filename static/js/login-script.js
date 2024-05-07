$(document).ready(function() {
    // Listen for form submission
    $('#submitBtn').on('click', function(event) {
        event.preventDefault(); // Prevent default form submission
        
        // Get the email and password values
        var email = $('#exampleInputEmail1').val();
        var password = $('#exampleInputPassword1').val();
        
        // Send a POST request to the login API
        $.ajax({
            url: '/login', // Replace with your login API URL
            type: 'POST',
            data: JSON.stringify({ email: email, password: password }),
            contentType: 'application/json',
            success: function(response) {
                // Handle successful login
                // console.log('Login successful:', response);
                // Redirect to another page, show success message, etc.
                document.write(response);

            },
            error: function(xhr, status, error) {
                // Handle login error
                console.error('Login failed:', error);
                // Show error message to the user, etc.
            }
        });
    });
});
