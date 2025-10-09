const dropdownButton = document.getElementById('dropdownButton');
const dropdownMenu = document.getElementById('dropdownMenu');
const dropdownIcon = document.getElementById('dropdownIcon');


dropdownButton.addEventListener('click', () => {
  dropdownMenu.classList.toggle('hidden');
  dropdownIcon.classList.toggle('rotate-180');
});

document.addEventListener('mousedown', (event) => {
  const dropdown = document.getElementById('dropdown');
  if (!dropdown.contains(event.target)) {
    dropdownMenu.classList.add('hidden');
    dropdownIcon.classList.remove('rotate-180');
  }
});