document.getElementById('searchInput')?.addEventListener('input', function (e) {
    const searchTerm = e.target.value.toLowerCase();
    const rows = document.querySelectorAll('.dossier-row');

    rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(searchTerm) ? '' : 'none';
    });
});

function exportTableToExcel() {
    alert('Fonctionnalité d\'export en cours de développement');
}

function printTable() {
    window.print();
}

function downloadDossier(id) {
    console.log('Téléchargement du dossier:', id);
}

function deleteDossier(id) {
    if (confirm('⚠️ ATTENTION : Cette action est irréversible !\n\nÊtes-vous sûr de vouloir supprimer définitivement ce dossier ?')) {
        console.log('Suppression du dossier:', id);
    }
}