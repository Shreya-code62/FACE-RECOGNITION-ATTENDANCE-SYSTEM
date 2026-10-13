document.addEventListener('DOMContentLoaded', () => {
  const menuToggle = document.getElementById('menuToggle');
  const sidebar = document.getElementById('sidebar');
  if (menuToggle && sidebar) {
    menuToggle.addEventListener('click', () => sidebar.classList.toggle('is-open'));
    sidebar.querySelectorAll('a').forEach((link) => link.addEventListener('click', () => sidebar.classList.remove('is-open')));
  }
  buildTimetable();
  setupFilters();
});

const timetableSlots = [
  '09:10 - 10:00', '10:00 - 10:50', '10:50 - 10:55', '10:55 - 11:45',
  '11:45 - 12:35', '12:35 - 01:25', '01:25 - 02:15', '02:15 - 03:05',
  '03:05 - 03:10', '03:10 - 04:00', '04:00 - 04:50'
];

function toMinutes(value) {
  const [hourText, minuteText] = value.trim().split(':');
  let hour = Number(hourText);
  if (hour <= 4) hour += 12;
  return hour * 60 + Number(minuteText);
}

function timeRange(value) {
  const [start, end] = value.split('-');
  return { start: toMinutes(start), end: toMinutes(end) };
}

function entryCoversSlot(entry, slot) {
  const entryRange = timeRange(entry.dataset.time);
  const slotRange = timeRange(slot);
  return entryRange.start <= slotRange.start && entryRange.end >= slotRange.end;
}

function facultyForEntry(entry) {
  const catalog = window.subjectCatalog || [];
  return (entry.dataset.code || '').split(' + ')
    .map((code) => catalog.find((subject) => subject.code === code)?.faculty)
    .filter(Boolean)
    .filter((faculty, index, list) => list.indexOf(faculty) === index)
    .join(' · ');
}

function buildTimetable() {
  const timetable = document.getElementById('weeklyTimetable');
  const body = document.getElementById('timetableBody');
  const sources = Array.from(document.querySelectorAll('.schedule-entry'));
  if (!timetable || !body || !sources.length) return;

  const days = Array.from(timetable.querySelectorAll('[data-day-header]')).map((header) => header.dataset.dayHeader);
  const today = new Date().toLocaleDateString('en-US', { weekday: 'long' });
  timetable.querySelectorAll('[data-day-header]').forEach((header) => {
    if (header.dataset.dayHeader === today) header.classList.add('is-today');
  });
  body.innerHTML = '';

  const todayEntries = sources.filter((entry) => entry.dataset.day === today && entry.dataset.kind === 'class');
  const todayValue = document.getElementById('todayClassesValue');
  const todayLabel = document.getElementById('todayClassesLabel');
  if (todayValue) todayValue.textContent = todayEntries.length;
  if (todayLabel) todayLabel.textContent = `${todayEntries.length} scheduled periods today`;

  timetableSlots.forEach((slot) => {
    const row = document.createElement('div');
    row.className = 'timetable-row';
    const timeCell = document.createElement('div');
    timeCell.className = 'timetable-time';
    timeCell.textContent = slot;
    row.appendChild(timeCell);
    days.forEach((day) => {
      const cell = document.createElement('div');
      cell.className = 'timetable-cell';
      const entry = sources.find((candidate) => candidate.dataset.day === day && entryCoversSlot(candidate, slot));
      if (!entry) {
        cell.classList.add('cell-empty');
        cell.innerHTML = '<span>—</span>';
      } else {
        cell.classList.add(`cell-${entry.dataset.kind}`);
        const faculty = facultyForEntry(entry);
        cell.innerHTML = `<strong>${entry.dataset.label}</strong>${entry.dataset.code ? `<span>${entry.dataset.code}</span>` : ''}${faculty ? `<small>${faculty}</small>` : ''}`;
        cell.title = faculty ? `${entry.dataset.label} · ${faculty}` : entry.dataset.label;
      }
      row.appendChild(cell);
    });
    body.appendChild(row);
  });
  updateNextClass(today, sources);
}

function updateNextClass(today, sources) {
  const container = document.getElementById('nextClassContent');
  if (!container) return;
  const now = new Date();
  const currentMinutes = now.getHours() * 60 + now.getMinutes();
  const next = sources
    .filter((entry) => entry.dataset.day === today && entry.dataset.kind === 'class')
    .map((entry) => ({ entry, range: timeRange(entry.dataset.time) }))
    .find(({ range }) => range.end > currentMinutes);
  if (!next) {
    container.innerHTML = '<strong>No more classes today</strong><span>Check the timetable for your next campus day</span>';
    return;
  }
  const faculty = facultyForEntry(next.entry);
  container.innerHTML = `<strong>${next.entry.dataset.label}</strong><span>${next.entry.dataset.time}${next.entry.dataset.code ? ` · ${next.entry.dataset.code}` : ''}</span>${faculty ? `<small>${faculty}</small>` : ''}`;
}

function setupFilters() {
  const filters = {
    date: document.getElementById('dateFilter'),
    subject: document.getElementById('subjectFilter'),
    status: document.getElementById('statusFilter')
  };
  const adminFilters = {
    date: document.getElementById('adminDateFilter'),
    branch: document.getElementById('adminBranchFilter'),
    section: document.getElementById('adminSectionFilter'),
    student: document.getElementById('adminStudentFilter'),
    status: document.getElementById('adminStatusFilter')
  };
  Object.values(filters).forEach((element) => {
    if (element) { element.addEventListener('input', applyStudentFilters); element.addEventListener('change', applyStudentFilters); }
  });
  Object.values(adminFilters).forEach((element) => {
    if (element) { element.addEventListener('input', applyAdminFilters); element.addEventListener('change', applyAdminFilters); }
  });

  function applyStudentFilters() {
    document.querySelectorAll('#attendanceSection tbody tr').forEach((row) => {
      const date = row.children[0]?.textContent?.trim() || '';
      const subject = row.children[1]?.textContent?.trim() || '';
      const status = row.children[5]?.textContent?.trim() || '';
      const matches = (!filters.date || !filters.date.value || date.includes(filters.date.value)) &&
        (!filters.subject || !filters.subject.value || subject.toLowerCase().includes(filters.subject.value.toLowerCase())) &&
        (!filters.status || !filters.status.value || status === filters.status.value);
      row.style.display = matches ? '' : 'none';
    });
  }

  function applyAdminFilters() {
    document.querySelectorAll('.admin-body tbody tr').forEach((row) => {
      const cells = Array.from(row.children);
      const student = cells[0]?.textContent?.trim() || '';
      const branch = cells[2]?.textContent?.trim() || '';
      const date = cells[5]?.textContent?.trim() || '';
      const status = cells[8]?.textContent?.trim() || '';
      const matches = (!adminFilters.date || !adminFilters.date.value || date.includes(adminFilters.date.value)) &&
        (!adminFilters.branch || !adminFilters.branch.value || branch.toLowerCase().includes(adminFilters.branch.value.toLowerCase())) &&
        (!adminFilters.student || !adminFilters.student.value || student.toLowerCase().includes(adminFilters.student.value.toLowerCase())) &&
        (!adminFilters.status || !adminFilters.status.value || status === adminFilters.status.value);
      row.style.display = matches ? '' : 'none';
    });
  }
}
