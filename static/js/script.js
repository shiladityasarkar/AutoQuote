document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('generateButton').addEventListener('click', function() {
        const fileInput = document.getElementById('fileInput');
        const file = fileInput.files[0];

        const gstValue = document.querySelector('input[name="gst"]:checked').value;
        const hsnValue = document.querySelector('input[name="hsn"]:checked').value;

        const formData = new FormData();
        formData.append('file', file);
        formData.append('gst', gstValue);
        formData.append('hsn', hsnValue);

        fetch('/generate', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            console.log('Success:', data);
        })
        .catch((error) => {
            console.error('Error:', error);
        });
    });
});