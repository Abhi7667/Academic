document.addEventListener('DOMContentLoaded', function() {
    // Get the delete modal element
    const deleteModal = new bootstrap.Modal(document.getElementById('deleteModal'));
    let deleteForm = document.getElementById('deleteForm');

    // Add click handlers to all delete buttons
    document.querySelectorAll('.delete-user').forEach(button => {
        button.addEventListener('click', function() {
            const userId = this.dataset.userId;
            deleteForm.action = `/admin/user/delete/${userId}`;
            deleteModal.show();
        });
    });

    // Add success message fade out
    document.querySelectorAll('.alert').forEach(alert => {
        setTimeout(() => {
            alert.classList.add('fade');
            setTimeout(() => alert.remove(), 300);
        }, 3000);
    });

    // Form validation
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });
});