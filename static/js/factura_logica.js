
let carrito = [];


document.getElementById('cai_selector').addEventListener('change', async (e) => {
    const idCai = e.target.value;
    const inputNumeroFactura = document.getElementById('numero_factura');
    const spanRTN = document.getElementById('rtn_text');
    const spanFechaVence = document.getElementById('fecha_f_text');

    if (!idCai) {
        inputNumeroFactura.value = "";
        spanRTN.innerText = "-";
        spanFechaVence.innerText = "-";
        return;
    }

    try {
       
        const response = await fetch(`/facturacion/get_cai_data/${idCai}`);
        const data = await response.json();

        if (data.rtn) {
        
            inputNumeroFactura.value = `000-000-01-${data.proximo}`;
            spanRTN.innerText = data.rtn;
            spanFechaVence.innerText = data.fecha_f;
            
            console.log("Datos CAI cargados:", data);
        }
    } catch (error) {
        console.error("Error al obtener datos del CAI:", error);
        alert("No se pudo conectar con el servidor para obtener datos del CAI.");
    }
});


function agregarAlCarrito() {
    const selector = document.getElementById('prod_selector');
    const optionSelected = selector.options[selector.selectedIndex];
    const inputCantidad = document.getElementById('cant_input');
    const cantidad = parseInt(inputCantidad.value);

    
    if (!optionSelected.value || isNaN(cantidad) || cantidad <= 0) {
        alert("Seleccione un producto y una cantidad válida.");
        return;
    }

    
    const stockDisponible = parseInt(optionSelected.dataset.stock);
    if (cantidad > stockDisponible) {
        alert(`Stock insuficiente. Solo hay ${stockDisponible} unidades disponibles.`);
        return;
    }

    
    const itemExistente = carrito.find(p => p.nombre === optionSelected.value);
    
    if (itemExistente) {
        if ((itemExistente.cantidad + cantidad) > stockDisponible) {
            alert("La cantidad total sumada supera el stock disponible.");
            return;
        }
        itemExistente.cantidad += cantidad;
        itemExistente.total = itemExistente.cantidad * itemExistente.precio;
    } else {
       
        const nuevoItem = {
            nombre: optionSelected.value,
            precio: parseFloat(optionSelected.dataset.precio),
            cantidad: cantidad,
            total: cantidad * parseFloat(optionSelected.dataset.precio)
        };
        carrito.push(nuevoItem);
    }

    
    inputCantidad.value = "";
    selector.value = "";
    renderizarTabla();
}


function renderizarTabla() {
    const tbody = document.getElementById('tabla_detalles');
    const btnGenerar = document.getElementById('btn-generar');
    tbody.innerHTML = "";
    let subtotalAcumulado = 0;

    carrito.forEach((item, index) => {
        subtotalAcumulado += item.total;
        
        const fila = `
            <tr>
                <td>${item.nombre}</td>
                <td class="text-center">${item.cantidad}</td>
                <td class="text-right">L. ${item.precio.toFixed(2)}</td>
                <td class="text-right"><strong>L. ${item.total.toFixed(2)}</strong></td>
                <td class="text-center">
                    <button type="button" class="btn btn-outline-danger btn-sm" onclick="eliminarItem(${index})">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            </tr>`;
        tbody.innerHTML += fila;
    });

   
    const impuesto = subtotalAcumulado * 0.25;
    const totalFinal = subtotalAcumulado + impuesto;

    document.getElementById('sub_view').innerText = subtotalAcumulado.toFixed(2);
    document.getElementById('isv_view').innerText = impuesto.toFixed(2);
    document.getElementById('total_view').innerText = totalFinal.toFixed(2);

    document.getElementById('productos_data').value = JSON.stringify(carrito);
    document.getElementById('subtotal_hidden').value = subtotalAcumulado.toFixed(2);
    document.getElementById('impuesto_hidden').value = impuesto.toFixed(2);
    document.getElementById('total_final_hidden').value = totalFinal.toFixed(2);
  
    const caiSeleccionado = document.getElementById('cai_selector').value;
    btnGenerar.disabled = (carrito.length === 0 || !caiSeleccionado);
}

function eliminarItem(index) {
    carrito.splice(index, 1);
    renderizarTabla();
}

document.getElementById('form-factura').onsubmit = function() {
    if (carrito.length === 0) {
        alert("Debe agregar al menos un producto a la factura.");
        return false;
    }
    return true; 
};