document.addEventListener('DOMContentLoaded', function() {

    document.getElementById("wait_str").style.visibility = "hidden";

    document.getElementById('generateButton').addEventListener('click', function() {
        document.getElementById("wait_str").style.visibility = "visible";
        const fileInput = document.getElementById('fileInput');
        const file = fileInput.files[0];

        // Get the GST and HSN values
        const gstValue = document.querySelector('input[name="gst"]:checked').value;
        const hsnValue = document.querySelector('input[name="hsn"]:checked').value;
        
        // Get selected price range (checkboxes)
        const priceRanges = [];
        document.querySelectorAll('input[name="reasonable"]:checked, input[name="moderate"]:checked, input[name="luxury"]:checked').forEach((checkbox) => {
            priceRanges.push(checkbox.value);
        });

        // Get the options value
        // const optionsValue = document.querySelector('input[name="options"]:checked').value;

        // Create formData and append values
        const formData = new FormData();
        formData.append('file', file);
        formData.append('gst', gstValue);
        formData.append('hsn', hsnValue);
        formData.append('priceRanges', JSON.stringify(priceRanges)); // sending as JSON string
        // formData.append('options', optionsValue);

        fetch('/generate', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.blob();
        })
        .then(blob => {
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            a.download = 'generated_quotation.xlsx';
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
        })
        .catch((error) => {
            console.error('Error:', error);
        });
    });
});
