// lb-filter por Lucas G. Bonato

const suplementstat_flt = ("Suplemento: [lb-filter v1.2]: ")

//FILTRO DE TABELA
function filterTable() {
    let input, table, select, filter, tbody, tr, td, i, txtValue;

    select = document.getElementById("filterSelect");
    input  = document.getElementById("filterInput");
    table  = document.getElementById("filterTable");

    tbody  = table.querySelector("tbody");
    tr     = tbody.getElementsByTagName("tr");
    filter = input.value.toUpperCase();
    index  = select.value;

    for (i = 0; i < tr.length; i++) {
        td = tr[i].getElementsByTagName("td")[index];
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
        // console.info('[INFO] lb-filter: A rota não contém filtros.');
    }
}


// OCULTAR FILTRO
function toggleFilter() {
    let container = document.getElementById('filter-container');
    let input = document.getElementById('filterInput');

    if (container.style.display === 'flex') {
        setFilterDisplay('none')
        return
    }
    setFilterDisplay('flex')
    input.focus();
    return
}

function setFilterDisplay(displayType) {
    let container = document.getElementById('filter-container');
    let filter = document.getElementById('table-filter');
    let auxFilters = document.querySelectorAll('.table-filter');

    container.style.display = displayType;
    filter.style.display = displayType;
    auxFilters.forEach(element => element.style.display = displayType);
    return
}

function addToFilterSelect(i, text) {
    let select = document.getElementById('filterSelect');
    select.innerHTML = `<option value="${i}">${text}</option>`;

    setFilterDisplay('flex');
    updateFilterIndex();
}

const headerCells = document.querySelectorAll("#filterTable thead th");

headerCells.forEach((th, index) => {
    th.addEventListener("click", () => {
        addToFilterSelect(index, th.innerText);
    });
    th.title = `Filtrar por: ${th.innerText}`;
    th.classList.add('hoverable');
});

