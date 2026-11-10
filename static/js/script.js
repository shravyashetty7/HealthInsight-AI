// Poll only rows whose AI remarks are still pending. The patient save itself is immediate.
document.addEventListener("DOMContentLoaded", () => {
  const pendingCells = Array.from(document.querySelectorAll("[data-patient-id][data-pending='true']"));
  if (!pendingCells.length) return;

  pendingCells.forEach((cell) => {
    const patientId = cell.dataset.patientId;
    const poll = async () => {
      try {
        const response = await fetch(`/patients/${patientId}/remarks-status`, { cache: "no-store" });
        if (!response.ok) return;
        const result = await response.json();
        cell.textContent = result.remarks;
        if (!result.pending) {
          cell.dataset.pending = "false";
          return;
        }
      } catch (error) {
        // Keep the page usable; the user can refresh later if polling is interrupted.
      }
      window.setTimeout(poll, 4000);
    };
    window.setTimeout(poll, 2500);
  });
});
