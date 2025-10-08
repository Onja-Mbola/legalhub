(() => {
  'use strict'
  const forms = document.querySelectorAll('.needs-validation')
  Array.from(forms).forEach(form => {
    form.addEventListener('submit', event => {
      if (!form.checkValidity()) {
        event.preventDefault()
        event.stopPropagation()
      }
      form.classList.add('was-validated')
    }, false)
  })
})()


function displayFileNames(input) {
        const fileList = document.getElementById('file-list');
        if (input.files.length > 0) {
            let html = '<div class="text-start mt-3"><p class="small fw-semibold text-success mb-2"><i class="fas fa-check me-2"></i>Fichiers sélectionnés :</p><ul class="list-unstyled small">';
            for (let i = 0; i < input.files.length; i++) {
                html += `<li class="mb-1"><i class="fas fa-file text-primary me-2"></i>${input.files[i].name}</li>`;
            }
            html += '</ul></div>';
            fileList.innerHTML = html;
        } else {
            fileList.innerHTML = '';
        }
    }