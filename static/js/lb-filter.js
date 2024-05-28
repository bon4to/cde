// lb-filter por Lucas Bonato
// versão: v1.0


const suplementstat_flt = ("Suplemento: [lb-filter v1.0]: ")

// console.log(suplementstat_flt + "Iniciando...")
try {
    let filterIndex = document.getElementById('filterSelect').value;
} catch (error) {
    console.info('Página não contém filtros:', error);
}
// console.log(suplementstat_flt + "Iniciado com sucesso. Pronto para ser utilizado")


//FILTRO DE TABELA
function filterTable() {

    let columnIndex = document.getElementById('filterSelect').value;
    let input, filter, table, tbody, tr, td, i, txtValue;
    input = document.querySelector(".searchInput");
    filter = input.value.toUpperCase();
    table = document.querySelector(".saldoTable");
    tbody = table.querySelector("tbody");
    tr = tbody.getElementsByTagName("tr");

    for (i = 0; i < tr.length; i++) {
        td = tr[i].getElementsByTagName("td")[columnIndex];
        if (td) {
            txtValue = td.textContent || td.innerText;
            if (txtValue.toUpperCase().indexOf(filter) > -1) {
                tr[i].style.display = "";
            } else {
                tr[i].style.display = "none";
            }
        }
    }
    // console.log(suplementstat_flt + "Elementos filtrados.");
}


// ATUALIZAR HEADER DE FILTRO
function updateFilterIndex() {
    try {
        // console.log(suplementstat_flt + "Atualizando...")
        let filterIndex = document.getElementById('filterSelect').value;
        // console.log(suplementstat_flt + "Filtrado por novo Parâmetro.")
        filterTable(filterIndex);
    } catch (error) {
        console.info('Página não contém filtros:', error);
    }
}


// OCULTAR FILTRO
function toggleFilter() {
    let filter = document.getElementById('table-filter');
    let input = document.getElementById('searchInput1');

    if (filter.style.display === 'flex') {
        filter.style.display = 'none';
    } else {
        filter.style.display = 'flex';
        input.focus();
    }
}

