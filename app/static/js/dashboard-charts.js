let chartDailyReg = null;
let chartDeptDist = null;
let chartDocStatus = null;
let chartBedOccupancy = null;
let chartDeptWait = null;

function renderDashboardCharts(deptId = '', days = 30) {
  const url = `/api/dashboard/charts?department_id=${deptId}&days=${days}`;
  
  fetch(url)
    .then(response => response.json())
    .then(data => {
      // 1. Daily Registrations Chart
      const ctxDaily = document.getElementById('chartDailyRegistrations');
      if (ctxDaily) {
        if (chartDailyReg) chartDailyReg.destroy();
        chartDailyReg = new Chart(ctxDaily, {
          type: 'line',
          data: {
            labels: data.daily_registrations.labels,
            datasets: [{
              label: 'New Patients',
              data: data.daily_registrations.values,
              borderColor: '#0284c7',
              backgroundColor: 'rgba(2, 132, 199, 0.1)',
              fill: true,
              tension: 0.35,
              pointBackgroundColor: '#0284c7',
              pointRadius: 4
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
              y: { beginAtZero: true, grid: { color: '#f1f5f9' } },
              x: { grid: { display: false } }
            }
          }
        });
      }

      // 2. Department Patient Distribution
      const ctxDept = document.getElementById('chartDeptDistribution');
      if (ctxDept) {
        if (chartDeptDist) chartDeptDist.destroy();
        chartDeptDist = new Chart(ctxDept, {
          type: 'bar',
          data: {
            labels: data.department_distribution.labels,
            datasets: [{
              label: 'Patients',
              data: data.department_distribution.values,
              backgroundColor: '#0d9488',
              borderRadius: 6
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
              y: { beginAtZero: true, grid: { color: '#f1f5f9' } },
              x: { grid: { display: false } }
            }
          }
        });
      }

      // 3. Doctor Availability Doughnut
      const ctxDoc = document.getElementById('chartDoctorAvailability');
      if (ctxDoc) {
        if (chartDocStatus) chartDocStatus.destroy();
        chartDocStatus = new Chart(ctxDoc, {
          type: 'doughnut',
          data: {
            labels: data.doctor_availability.labels,
            datasets: [{
              data: data.doctor_availability.values,
              backgroundColor: ['#10b981', '#f59e0b', '#64748b', '#ef4444'],
              borderWidth: 2
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              legend: { position: 'bottom' }
            },
            cutout: '65%'
          }
        });
      }

      // 4. Bed Occupancy Stacked Bar
      const ctxBed = document.getElementById('chartBedOccupancy');
      if (ctxBed) {
        if (chartBedOccupancy) chartBedOccupancy.destroy();
        chartBedOccupancy = new Chart(ctxBed, {
          type: 'bar',
          data: {
            labels: data.bed_occupancy.labels,
            datasets: [
              {
                label: 'Occupied Beds',
                data: data.bed_occupancy.occupied,
                backgroundColor: '#ef4444',
                borderRadius: 4
              },
              {
                label: 'Available Beds',
                data: data.bed_occupancy.available,
                backgroundColor: '#10b981',
                borderRadius: 4
              }
            ]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
              x: { stacked: true, grid: { display: false } },
              y: { stacked: true, beginAtZero: true, grid: { color: '#f1f5f9' } }
            }
          }
        });
      }

      // 5. Department Waiting Times
      const ctxWait = document.getElementById('chartDeptWaitingTimes');
      if (ctxWait) {
        if (chartDeptWait) chartDeptWait.destroy();
        chartDeptWait = new Chart(ctxWait, {
          type: 'bar',
          data: {
            labels: data.department_waiting_times.labels,
            datasets: [{
              label: 'Avg Waiting Time (Minutes)',
              data: data.department_waiting_times.values,
              backgroundColor: '#6366f1',
              borderRadius: 6
            }]
          },
          options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
              x: { beginAtZero: true, grid: { color: '#f1f5f9' } },
              y: { grid: { display: false } }
            }
          }
        });
      }
    })
    .catch(err => console.error('Error fetching dashboard chart data:', err));
}

document.addEventListener('DOMContentLoaded', function () {
  if (document.getElementById('chartDailyRegistrations')) {
    renderDashboardCharts();

    const deptFilter = document.getElementById('dashboardDeptFilter');
    if (deptFilter) {
      deptFilter.addEventListener('change', function () {
        renderDashboardCharts(this.value);
      });
    }
  }
});

