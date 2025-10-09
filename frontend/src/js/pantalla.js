/* document.addEventListener("DOMContentLoaded", function() {
    window.ticket = function () {
        const contenedor = document.getElementById("contenedor");
        
        // Create and append the first ticket row
        const ticket1 = document.createElement("tr");
        ticket1.classList.add("bg-slate-50", "border-b", "border-slate-200", "hover:bg-slate-100", "transition-colors");
        ticket1.innerHTML = `
            <td class="px-4 sm:px-6 md:px-8 py-3 sm:py-4 text-emerald-700 font-bold text-xl sm:text-2xl">S-101</td>
            <td class="px-4 sm:px-6 md:px-8 py-3 sm:py-4 text-slate-700 font-medium text-sm sm:text-lg">Servicios Escolares</td>
            <td class="px-4 sm:px-6 md:px-8 py-3 sm:py-4 text-slate-700 font-medium text-sm sm:text-lg">Ventanilla 1</td>
        `;
        contenedor.appendChild(ticket1);
        
        // Create and append the second ticket row
        const ticket2 = document.createElement("tr");
        ticket2.classList.add("bg-white", "border-b", "border-slate-200", "hover:bg-slate-100", "transition-colors");
        ticket2.innerHTML = `
            <td class="px-4 sm:px-6 md:px-8 py-3 sm:py-4 text-emerald-700 font-bold text-xl sm:text-2xl">B-102</td>
            <td class="px-4 sm:px-6 md:px-8 py-3 sm:py-4 text-slate-700 font-medium text-sm sm:text-lg">Becas</td>
            <td class="px-4 sm:px-6 md:px-8 py-3 sm:py-4 text-slate-700 font-medium text-sm sm:text-lg">Ventanilla 1</td>
        `;
        contenedor.appendChild(ticket2);
        
        // Create and append the third ticket row
        const ticket3 = document.createElement("tr");
        ticket3.classList.add("bg-slate-50", "border-b", "border-slate-200", "hover:bg-slate-100", "transition-colors");
        ticket3.innerHTML = `
            <td class="px-4 sm:px-6 md:px-8 py-3 sm:py-4 text-emerald-700 font-bold text-xl sm:text-2xl">C-103</td>
            <td class="px-4 sm:px-6 md:px-8 py-3 sm:py-4 text-slate-700 font-medium text-sm sm:text-lg">Cajas</td>
            <td class="px-4 sm:px-6 md:px-8 py-3 sm:py-4 text-slate-700 font-medium text-sm sm:text-lg">Ventanilla 2</td>
        `;
        contenedor.appendChild(ticket3);
        
        // Create and append the fourth ticket row
        const ticket4 = document.createElement("tr");
        ticket4.classList.add("bg-white", "border-b", "border-slate-200", "hover:bg-slate-100", "transition-colors");
        ticket4.innerHTML = `
            <td class="px-4 sm:px-6 md:px-8 py-3 sm:py-4 text-emerald-700 font-bold text-xl sm:text-2xl">C-104</td>
            <td class="px-4 sm:px-6 md:px-8 py-3 sm:py-4 text-slate-700 font-medium text-sm sm:text-lg">Becas</td>
            <td class="px-4 sm:px-6 md:px-8 py-3 sm:py-4 text-slate-700 font-medium text-sm sm:text-lg">Por asignar</td>
        `;
        contenedor.appendChild(ticket4);
    }
}); */