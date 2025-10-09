const form = document.getElementById('empleadoForm');
const tabla = document.getElementById('tablaEmpleados');
let contador = 0;

form.addEventListener('submit', (e) => {
  e.preventDefault();

  const nombre = document.getElementById('nombre').value.trim();
  const apellido = document.getElementById('apellido').value.trim();
  const sector = document.getElementById('sector').value;

  if (!nombre || !apellido || !sector) return;

  contador++;

  const fila = document.createElement('tr');
  fila.classList.add('border-b');
  fila.innerHTML = `
    <td class="px-4 py-2 border border-gray-300">${contador}</td>
    <td class="px-4 py-2 border border-gray-300">${nombre} ${apellido}</td>
    <td class="px-4 py-2 border border-gray-300">${sector}</td>
  `;

  tabla.appendChild(fila);

  form.reset();
});