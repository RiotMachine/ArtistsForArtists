$(document).ready(function () {
    $('#dataTable').DataTable();
});

$('#dataTable').DataTable({
    columnDefs: [{ orderable: false, targets: 0 }],
    order: []
})