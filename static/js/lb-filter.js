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
    orderTableBy(i);
    text = text.replace(/[\u25B2\u25BC]/g, '').trim()
    let select = document.getElementById('filterSelect');
    select.innerHTML = `<option value="${i}">${text}</option>`;

    setFilterDisplay('flex');
    updateFilterIndex();
}

let sortDirections = {};

function orderTableBy(i) {
    const table = document.getElementById("filterTable");
    const thead = table.tHead;
    const tbody = table.tBodies[0];
    const rows = Array.from(tbody.rows);

    // alternar direção
    const currentDirection = sortDirections[i] || "asc";
    const newDirection = currentDirection === "asc" ? "desc" : "asc";
    sortDirections[i] = newDirection;

    // detectar se é número
    const isNumberColumn = rows
        .map(row => row.cells[i].innerText.trim())
        .filter(val => val !== '' && val.toUpperCase() !== 'N/A')
        .every(val => !isNaN(parseFloat(val)));

    function isDateISO(str) {
        return /^\d{4}-\d{2}-\d{2}$/.test(str);
    }

    rows.sort((a, b) => {
        let x = a.cells[i].innerText.trim();
        let y = b.cells[i].innerText.trim();

        const isNAx = x === '' || x.toUpperCase() === 'N/A';
        const isNAy = y === '' || y.toUpperCase() === 'N/A';

        if (isNAx && !isNAy) return 1;
        if (!isNAx && isNAy) return -1;
        if (isNAx && isNAy) return 0;

        // verifica se ambos são datas válidas (YYYY-MM-DD)
        if (isDateISO(x) && isDateISO(y)) {
            x = new Date(x);
            y = new Date(y);
        }
        // verifica se são números (após confirmar que não são datas)
        else if (!isNaN(x) && !isNaN(y)) {
            x = parseFloat(x);
            y = parseFloat(y);
        }

        if (x < y) return newDirection === "asc" ? -1 : 1;
        if (x > y) return newDirection === "asc" ? 1 : -1;
        return 0;
    });

    // reanexar as linhas
    rows.forEach(row => tbody.appendChild(row));

    // atualizar ícones de ordenação
    const headers = thead.rows[0].cells;
    for (let j = 0; j < headers.length; j++) {
        // remove setas antigas
        let baseText = headers[j].innerText.replace(/[\u25B2\u25BC]/g, '').trim(); 
        headers[j].innerHTML = baseText;
        if (j === i) {
            const arrow = newDirection === "asc" ? "▲" : "▼";
            headers[j].innerHTML += ` <span style="font-size: 0.6em;">${arrow}</span>`;
        }
    }
}

const headerCells = document.querySelectorAll("#filterTable thead th");

headerCells.forEach((th, index) => {
    th.addEventListener("click", () => {
        addToFilterSelect(index, th.innerText);
    });
    th.title = `Filtrar por: ${th.innerText}`;
    th.classList.add('hoverable');
});
