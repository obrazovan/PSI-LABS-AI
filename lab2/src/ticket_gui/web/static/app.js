/**
 * Client-side Controller for Academic Examination Registrar.
 * Clean Code Architecture: modular, strictly separated, observable state.
 */

(function () {
  'use strict';

  // --- DOM Elements ---
  const themeToggle = document.getElementById('themeToggle');
  const soundToggle = document.getElementById('soundToggle');
  const soundIcon = document.getElementById('soundIcon');

  const pillStudents = document.getElementById('pillStudents');
  const pillTickets = document.getElementById('pillTickets');
  const pillResults = document.getElementById('pillResults');

  const groupSelect = document.getElementById('groupSelect');
  const studentSelect = document.getElementById('studentSelect');
  const generateBtn = document.getElementById('generateBtn');
  const emptyGroupNote = document.getElementById('emptyGroupNote');
  const statusDot = document.getElementById('statusDot');
  const statusText = document.getElementById('statusText');

  const alertBanner = document.getElementById('alertBanner');
  const alertTitle = document.getElementById('alertTitle');
  const alertMessage = document.getElementById('alertMessage');
  const alertRetryBtn = document.getElementById('alertRetryBtn');
  const alertCloseBtn = document.getElementById('alertCloseBtn');

  const resultModal = document.getElementById('resultModal');
  const modalTicketNumber = document.getElementById('modalTicketNumber');
  const modalStudentName = document.getElementById('modalStudentName');
  const modalStudentGroup = document.getElementById('modalStudentGroup');
  const modalIssuedTime = document.getElementById('modalIssuedTime');
  const modalRepeatBanner = document.getElementById('modalRepeatBanner');
  const modalQuestionsList = document.getElementById('modalQuestionsList');
  const modalCloseBtn = document.getElementById('modalCloseBtn');
  const modalPrintBtn = document.getElementById('modalPrintBtn');
  const ticketSecurityHash = document.getElementById('ticketSecurityHash');

  const historyTbody = document.getElementById('historyTbody');
  const historySearchInput = document.getElementById('historySearchInput');
  const refreshHistoryBtn = document.getElementById('refreshHistoryBtn');
  const archiveMeta = document.getElementById('archiveMeta');

  // --- State ---
  let currentStudents = [];
  let selectedStudent = null;
  let lastFailedAction = null;
  let historyRecords = [];
  let soundEnabled = true;

  // --- 1. Audio Haptics (Web Audio API) ---
  let audioCtx = null;

  function initAudio() {
    const savedSound = localStorage.getItem('sound_enabled');
    soundEnabled = savedSound !== 'false';
    updateSoundIcon();

    soundToggle.addEventListener('click', toggleSound);
  }

  function toggleSound() {
    soundEnabled = !soundEnabled;
    localStorage.setItem('sound_enabled', String(soundEnabled));
    updateSoundIcon();
  }

  function updateSoundIcon() {
    soundIcon.textContent = soundEnabled ? '🔊' : '🔇';
  }

  function playPaperSound() {
    if (!soundEnabled) return;
    try {
      if (!audioCtx) {
        audioCtx = new (window.AudioContext || window.webkitAudioContext)();
      }
      if (audioCtx.state === 'suspended') {
        audioCtx.resume();
      }

      // Синтез мягкого тактильного звука штампа/бумаги
      const osc = audioCtx.createOscillator();
      const gain = audioCtx.createGain();

      osc.type = 'triangle';
      osc.frequency.setValueAtTime(140, audioCtx.currentTime);
      osc.frequency.exponentialRampToValueAtTime(45, audioCtx.currentTime + 0.12);

      gain.gain.setValueAtTime(0.2, audioCtx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.12);

      osc.connect(gain);
      gain.connect(audioCtx.destination);

      osc.start();
      osc.stop(audioCtx.currentTime + 0.13);
    } catch (_) {
      // Игнорируем ограничения автовоспроизведения
    }
  }

  // --- 2. Theme Management ---
  function initTheme() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    setTheme(savedTheme);

    themeToggle.addEventListener('click', () => {
      const current = document.documentElement.getAttribute('data-theme') || 'light';
      const next = current === 'dark' ? 'light' : 'dark';
      setTheme(next);
    });
  }

  function setTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
  }

  // --- 3. Status & Alert Presentation ---
  function setStatus(text, type = 'idle') {
    statusText.textContent = text;
    statusDot.className = 'academic-dot';
    if (type === 'ready') statusDot.classList.add('dot-ready');
    else if (type === 'error') statusDot.classList.add('dot-error');
    else statusDot.classList.add('dot-idle');
  }

  function showAlert(title, message, isRetryable = false, retryAction = null) {
    alertTitle.textContent = title;
    alertMessage.textContent = message;
    alertBanner.classList.remove('hidden');

    if (isRetryable && retryAction) {
      lastFailedAction = retryAction;
      alertRetryBtn.classList.remove('hidden');
    } else {
      lastFailedAction = null;
      alertRetryBtn.classList.add('hidden');
    }
  }

  function hideAlert() {
    alertBanner.classList.add('hidden');
    lastFailedAction = null;
  }

  alertCloseBtn.addEventListener('click', hideAlert);
  alertRetryBtn.addEventListener('click', () => {
    hideAlert();
    if (typeof lastFailedAction === 'function') {
      lastFailedAction();
    }
  });

  // --- 4. API Communication & Initial Setup ---
  async function fetchInit() {
    setStatus('Подключение к архиву и чтение реестра...', 'idle');
    try {
      const resp = await fetch('/api/init');
      const data = await resp.json();

      if (!resp.ok) {
        if (resp.status === 423) {
          showAlert('Файл заблокирован', data.message, true, fetchInit);
          setStatus('⚠️ Файл results.xlsx заблокирован в Microsoft Excel!', 'error');
          return;
        }
        throw new Error(data.message || 'Ошибка инициализации');
      }

      updateSourcePills(data);

      if (!data.ready) {
        const missing = (data.missing_sources || []).join(', ');
        showAlert('Входные материалы не обнаружены', `Не найдены обязательные файлы: ${missing}. Проверьте наличие students.xlsx и tickets.docx.`);
        setStatus('⚠️ Входные источники не найдены!', 'error');
        groupSelect.innerHTML = '<option value="" disabled selected>— Источники не найдены —</option>';
        return;
      }

      populateGroups(data.groups);
      setStatus(`● Готово: групп — ${data.groups_count}, валидных билетов — ${data.tickets_count}`, 'ready');
      loadHistory();
    } catch (err) {
      showAlert('Ошибка связи с сервером', err.message);
      setStatus('Не удалось установить соединение с сервером', 'error');
    }
  }

  function updateSourcePills(initData) {
    const missing = initData.missing_sources || [];
    const hasStudents = !missing.some((s) => s.toLowerCase().includes('student'));
    const hasTickets = !missing.some((s) => s.toLowerCase().includes('ticket'));

    pillStudents.classList.toggle('pill-missing', !hasStudents);
    pillTickets.classList.toggle('pill-missing', !hasTickets);
    pillResults.classList.remove('pill-missing');
  }

  function populateGroups(groups) {
    if (!groups || groups.length === 0) {
      groupSelect.innerHTML = '<option value="" disabled selected>— Нет доступных групп —</option>';
      setStatus('В файле students.xlsx нет листов с группами', 'idle');
      return;
    }

    groupSelect.innerHTML = '<option value="" disabled selected>— Выберите академическую группу —</option>';
    groups.forEach((g) => {
      const opt = document.createElement('option');
      opt.value = g;
      opt.textContent = g;
      groupSelect.appendChild(opt);
    });

    groupSelect.disabled = false;
  }

  async function onGroupChange() {
    const selectedGroup = groupSelect.value;
    if (!selectedGroup) return;

    resetStudentSelection();
    setStatus(`Чтение состава группы '${selectedGroup}'...`, 'idle');

    try {
      const resp = await fetch(`/api/students?group=${encodeURIComponent(selectedGroup)}`);
      const data = await resp.json();

      if (!resp.ok) throw new Error(data.message || 'Ошибка загрузки студентов');

      currentStudents = data.students || [];

      if (currentStudents.length === 0) {
        studentSelect.innerHTML = '<option value="" disabled selected>— В группе нет зарегистрированных студентов —</option>';
        studentSelect.disabled = true;
        emptyGroupNote.classList.remove('hidden');
        generateBtn.disabled = true;
        setStatus(`⚠️ В группе '${selectedGroup}' нет студентов`, 'idle');
        return;
      }

      emptyGroupNote.classList.add('hidden');
      studentSelect.innerHTML = '<option value="" disabled selected>— Выберите студента из списка —</option>';
      currentStudents.forEach((st, idx) => {
        const opt = document.createElement('option');
        opt.value = String(idx);
        opt.textContent = st.full_name;
        studentSelect.appendChild(opt);
      });

      studentSelect.disabled = false;
      generateBtn.disabled = true;
      setStatus(`Группа '${selectedGroup}': ${currentStudents.length} студентов. Выберите экзаменуемого.`, 'idle');
    } catch (err) {
      showAlert('Ошибка чтения списка', err.message);
      setStatus('Не удалось загрузить студентов', 'error');
    }
  }

  function onStudentChange() {
    const idx = parseInt(studentSelect.value, 10);
    if (!isNaN(idx) && idx >= 0 && idx < currentStudents.length) {
      selectedStudent = currentStudents[idx];
      generateBtn.disabled = false;
      setStatus(`● Экзаменуемый: ${selectedStudent.full_name}. Нажмите кнопку выдачи билета.`, 'ready');
    } else {
      selectedStudent = null;
      generateBtn.disabled = true;
    }
  }

  function resetStudentSelection() {
    selectedStudent = null;
    currentStudents = [];
    studentSelect.innerHTML = '<option value="" disabled selected>— Сначала выберите группу —</option>';
    studentSelect.disabled = true;
    emptyGroupNote.classList.add('hidden');
    generateBtn.disabled = true;
  }

  // --- 5. Ticket Generation Action ---
  async function generateTicket() {
    if (!selectedStudent) return;

    generateBtn.disabled = true;
    const originalText = generateBtn.querySelector('.btn-text').textContent;
    generateBtn.querySelector('.btn-text').textContent = 'Оформление бланка...';

    const payload = {
      group: selectedStudent.group,
      last_name: selectedStudent.last_name,
      first_name: selectedStudent.first_name,
    };

    try {
      const resp = await fetch('/api/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      const data = await resp.json();

      if (!resp.ok) {
        if (resp.status === 423) {
          showAlert(
            'Файл заблокирован',
            'Файл results.xlsx открыт в Microsoft Excel. Закройте его и нажмите "Повторить попытку".',
            true,
            generateTicket
          );
          return;
        }
        throw new Error(data.message || 'Ошибка генерации билета');
      }

      playPaperSound();
      showResultModal(data.ticket, data.result);

      const repeatMark = data.result.is_repeat ? ' (ДУБЛИКАТ)' : '';
      setStatus(`✓ Билет №${data.ticket.number} выписан для ${data.result.full_name}${repeatMark}`, 'ready');
      loadHistory();
    } catch (err) {
      showAlert('Ошибка оформления', err.message);
      setStatus('Не удалось сформировать билет', 'error');
    } finally {
      generateBtn.disabled = !selectedStudent;
      generateBtn.querySelector('.btn-text').textContent = originalText;
    }
  }

  // --- 6. Authentic Ticket Modal Presentation ---
  function showResultModal(ticket, result) {
    modalTicketNumber.textContent = `Ваш билет № ${ticket.number}`;
    modalStudentName.textContent = `Студент: ${result.full_name}`;
    modalStudentGroup.textContent = `Группа: ${result.group}`;
    modalIssuedTime.textContent = result.timestamp || new Date().toLocaleString('ru-RU');

    // Хеш аутентификации бланка
    const hash = ((ticket.number * 997 + result.full_name.length * 37) % 65536).toString(16).toUpperCase();
    ticketSecurityHash.textContent = `EXAM-SEC-HASH-0x${hash.padStart(4, '0')}`;

    if (result.is_repeat) {
      modalRepeatBanner.classList.remove('hidden');
    } else {
      modalRepeatBanner.classList.add('hidden');
    }

    modalQuestionsList.innerHTML = '';
    (ticket.questions || []).forEach((qText, index) => {
      const card = document.createElement('div');
      card.className = 'question-card';

      const badge = document.createElement('span');
      badge.className = 'question-badge';
      badge.textContent = `Вопрос ${index + 1}`;

      const text = document.createElement('div');
      text.className = 'question-text';
      text.textContent = qText;

      card.appendChild(badge);
      card.appendChild(text);
      modalQuestionsList.appendChild(card);
    });

    resultModal.classList.remove('hidden');
    modalCloseBtn.focus();
  }

  function closeModal() {
    resultModal.classList.add('hidden');
    generateBtn.focus();
  }

  function isModalOpen() {
    return !resultModal.classList.contains('hidden');
  }

  modalCloseBtn.addEventListener('click', closeModal);
  modalPrintBtn.addEventListener('click', () => {
    window.print();
  });

  // --- 7. History Ledger Presentation ---
  async function loadHistory() {
    try {
      const resp = await fetch('/api/history');
      if (!resp.ok) return;

      const data = await resp.json();
      historyRecords = data.history || [];
      renderHistoryTable(historyRecords);
      archiveMeta.textContent = `Записей в реестре: ${historyRecords.length}`;
    } catch (_) {
      // Тихо игнорируем ошибку фонового обновления
    }
  }

  function renderHistoryTable(records) {
    if (!records || records.length === 0) {
      historyTbody.innerHTML = '<tr><td colspan="5" class="table-empty">Журнал выдач пока пуст</td></tr>';
      return;
    }

    const filterText = (historySearchInput.value || '').trim().toLowerCase();
    const filtered = records.filter((r) => {
      if (!filterText) return true;
      const combined = `${r.group} ${r.last_name} ${r.first_name}`.toLowerCase();
      return combined.includes(filterText);
    });

    if (filtered.length === 0) {
      historyTbody.innerHTML = '<tr><td colspan="5" class="table-empty">Ничего не найдено по запросу</td></tr>';
      return;
    }

    historyTbody.innerHTML = '';
    filtered.forEach((r) => {
      const tr = document.createElement('tr');

      const isRepeat = r.is_repeat || r.repeat_str === 'да';
      const statusBadge = isRepeat
        ? '<span class="status-badge-repeat">Повтор</span>'
        : '<span class="status-badge-initial">Первичный</span>';

      tr.innerHTML = `
        <td><strong>${escapeHtml(r.group)}</strong></td>
        <td>${escapeHtml(r.last_name)} ${escapeHtml(r.first_name)}</td>
        <td><span style="font-family: var(--font-mono); font-weight: 700;">№ ${r.ticket_number}</span></td>
        <td style="font-family: var(--font-mono); font-size: 11px; color: var(--ink-muted);">${escapeHtml(r.timestamp)}</td>
        <td>${statusBadge}</td>
      `;
      historyTbody.appendChild(tr);
    });
  }

  function escapeHtml(str) {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  historySearchInput.addEventListener('input', () => {
    renderHistoryTable(historyRecords);
  });

  refreshHistoryBtn.addEventListener('click', loadHistory);

  // --- 8. Event Listeners & Keyboard Shortcuts ---
  groupSelect.addEventListener('change', onGroupChange);
  studentSelect.addEventListener('change', onStudentChange);
  generateBtn.addEventListener('click', generateTicket);

  window.addEventListener('keydown', (e) => {
    // ESC закрывает модальное окно результата (AC-5)
    if (e.key === 'Escape' && isModalOpen()) {
      e.preventDefault();
      closeModal();
      return;
    }

    // Если фокус в текстовом поле поиска, не перехватываем горячие клавиши
    if (document.activeElement === historySearchInput) {
      return;
    }

    if (e.key === 'Enter' && !isModalOpen() && !generateBtn.disabled) {
      e.preventDefault();
      generateTicket();
    } else if (e.key === '1' && !isModalOpen()) {
      groupSelect.focus();
    } else if (e.key === '2' && !isModalOpen() && !studentSelect.disabled) {
      studentSelect.focus();
    } else if ((e.key === 'p' || e.key === 'P' || e.key === 'з' || e.key === 'З') && isModalOpen()) {
      e.preventDefault();
      window.print();
    } else if (e.key === 'd' || e.key === 'D' || e.key === 'в' || e.key === 'В') {
      themeToggle.click();
    } else if (e.key === 'm' || e.key === 'M' || e.key === 'ь' || e.key === 'Ь') {
      toggleSound();
    }
  });

  // --- 9. Bootstrap Application ---
  initTheme();
  initAudio();
  fetchInit();
})();
