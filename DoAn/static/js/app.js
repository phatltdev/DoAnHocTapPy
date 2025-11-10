$(document).ready(function() {
    const apiUrl = 'http://127.0.0.1:5000/api';

    // --- Modal Stacking Manager ---
    $(document).on('show.bs.modal', '.modal', function () {
        const zIndex = 1040 + (10 * $('.modal:visible').length);
        $(this).css('z-index', zIndex);
        setTimeout(() => $('.modal-backdrop').not('.modal-stack').css('z-index', zIndex - 1).addClass('modal-stack'));
    });

    // Load patients on page load
    loadPatients();

    function loadPatients() {
        $.get(`${apiUrl}/patients`, function(data) {
            let html = '';
            data.forEach(patient => {
                html += `
                    <tr>
                        <td>${patient.id}</td>
                        <td>${patient.patient_code}</td>
                        <td>${patient.name}</td>
                        <td>${patient.age}</td>
                        <td>${patient.address}</td>
                        <td>${patient.phone}</td>
                        <td>${patient.email}</td>
                        <td>
                            <button class="btn btn-sm btn-primary add-test" data-id="${patient.id}">Add Test</button>
                            <button class="btn btn-sm btn-info view-forms" data-id="${patient.id}">View Forms</button>
                            <button class="btn btn-sm btn-warning edit-patient" data-id="${patient.id}">Edit</button>
                            <button class="btn btn-sm btn-danger delete-patient" data-id="${patient.id}">Delete</button>
                        </td>
                    </tr>
                `;
            });
            $('#patientTableBody').html(html);
        });
    }

    // Handle Add Patient button click
    $('#addPatientBtn').click(function() {
        $('#patientForm')[0].reset();
        $('#patientId').val('');
        $('#patientModalLabel').text('Add Patient');
    });

    // Handle Patient form submission
    $('#patientForm').submit(function(e) {
        e.preventDefault();
        const patientId = $('#patientId').val();
        const patientData = {
            patient_code: $('#patientCode').val(),
            name: $('#patientName').val(),
            age: $('#patientAge').val(),
            address: $('#patientAddress').val(),
            phone: $('#patientPhone').val(),
            email: $('#patientEmail').val(),
        };

        const method = patientId ? 'PUT' : 'POST';
        const url = patientId ? `${apiUrl}/patients/${patientId}` : `${apiUrl}/patients`;

        $.ajax({
            url: url,
            method: method,
            contentType: 'application/json',
            data: JSON.stringify(patientData),
            success: function() {
                $('#patientModal').modal('hide');
                loadPatients();
            }
        });
    });

    // Handle Edit Patient button click
    $(document).on('click', '.edit-patient', function() {
        const patientId = $(this).attr('data-id');
        $.get(`${apiUrl}/patients/${patientId}`, function(patient) {
            $('#patientId').val(patient.id);
            $('#patientCode').val(patient.patient_code);
            $('#patientName').val(patient.name);
            $('#patientAge').val(patient.age);
            $('#patientAddress').val(patient.address);
            $('#patientPhone').val(patient.phone);
            $('#patientEmail').val(patient.email);
            $('#patientModalLabel').text('Edit Patient');
            $('#patientModal').modal('show');
        });
    });

    // Handle Delete Patient button click
    $(document).on('click', '.delete-patient', function() {
        const patientId = $(this).attr('data-id');
        if (confirm('Are you sure you want to delete this patient?')) {
            $.ajax({
                url: `${apiUrl}/patients/${patientId}`,
                method: 'DELETE',
                success: function() {
                    loadPatients();
                }
            });
        }
    });

    // Handle Add Test button click
    $(document).on('click', '.add-test', function() {
        const patientId = $(this).attr('data-id');
        $('#addTestForm')[0].reset();
        $('#addTestFormPatientId').val(patientId);
        $('#addTestFormModal').modal('show');
    });

    // Handle Add Test Form submission
    $('#addTestForm').submit(function(e) {
        e.preventDefault();
        const testFormData = {
            form_number: $('#formNumber').val(),
            patient_id: $('#addTestFormPatientId').val(),
        };

        $.ajax({
            url: `${apiUrl}/test_forms`,
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify(testFormData),
            success: function() {
                $('#addTestFormModal').modal('hide');
            }
        });
    });

    // Handle Edit Test Form button click
    $(document).on('click', '.edit-test-form', function() {
        const formId = $(this).attr('data-id');
        $.get(`${apiUrl}/test_forms/${formId}`, function(form) {
            $('#editTestFormId').val(form.id);
            $('#editFormNumber').val(form.form_number);
            $('#editTestFormModal').modal('show');
        });
    });

    // Handle Edit Test Form submission
    $('#editTestForm').submit(function(e) {
        e.preventDefault();
        const formId = $('#editTestFormId').val();
        const testFormData = {
            form_number: $('#editFormNumber').val(),
        };

        $.ajax({
            url: `${apiUrl}/test_forms/${formId}`,
            method: 'PUT',
            contentType: 'application/json',
            data: JSON.stringify(testFormData),
            success: function() {
                $('#editTestFormModal').modal('hide');
                $('#testFormModal').modal('hide');
            }
        });
    });

    // Handle Delete Test Form button click
    $(document).on('click', '.delete-test-form', function() {
        const formId = $(this).attr('data-id');
        if (confirm('Are you sure you want to delete this test form?')) {
            $.ajax({
                url: `${apiUrl}/test_forms/${formId}`,
                method: 'DELETE',
                success: function() {
                    $('#testFormModal').modal('hide');
                }
            });
        }
    });

    // Handle Add Test Detail button click
    $(document).on('click', '.add-test-detail', function() {
        const testFormId = $(this).attr('data-id');
        $('#addTestDetailForm')[0].reset();
        $('#addTestDetailTestFormId').val(testFormId);
        $('#addTestDetailModal').modal('show');
    });

    // Handle Add Test Detail Form submission
    $('#addTestDetailForm').submit(function(e) {
        e.preventDefault();
        const testDetailData = {
            test_name: $('#testName').val(),
            result: $('#result').val(),
            test_form_id: $('#addTestDetailTestFormId').val(),
        };

        $.ajax({
            url: `${apiUrl}/test_details`,
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify(testDetailData),
            success: function() {
                $('#addTestDetailModal').modal('hide');
            }
        });
    });

    // Handle Edit Test Detail button click
    $(document).on('click', '.edit-test-detail', function() {
        const detailId = $(this).attr('data-id');
        $.get(`${apiUrl}/test_details/${detailId}`, function(detail) {
            $('#editTestDetailId').val(detail.id);
            $('#editTestName').val(detail.test_name);
            $('#editResult').val(detail.result);
            $('#editTestDetailModal').modal('show');
        });
    });

    // Handle Edit Test Detail submission
    $('#editTestDetailForm').submit(function(e) {
        e.preventDefault();
        const detailId = $('#editTestDetailId').val();
        const testDetailData = {
            test_name: $('#editTestName').val(),
            result: $('#editResult').val(),
        };

        $.ajax({
            url: `${apiUrl}/test_details/${detailId}`,
            method: 'PUT',
            contentType: 'application/json',
            data: JSON.stringify(testDetailData),
            success: function() {
                $('#editTestDetailModal').modal('hide');
                $('#testDetailModal').modal('hide');
            }
        });
    });

    // Handle Delete Test Detail button click
    $(document).on('click', '.delete-test-detail', function() {
        const detailId = $(this).attr('data-id');
        if (confirm('Are you sure you want to delete this test detail?')) {
            $.ajax({
                url: `${apiUrl}/test_details/${detailId}`,
                method: 'DELETE',
                success: function() {
                    $('#testDetailModal').modal('hide');
                }
            });
        }
    });

    // Handle View Forms button click
    $(document).on('click', '.view-forms', function() {
        const patientId = $(this).attr('data-id');
        $.get(`${apiUrl}/patients/${patientId}`, function(patient) {
            let html = '';
            patient.test_forms.forEach(form => {
                html += `
                    <tr>
                        <td>${form.id}</td>
                        <td>${form.form_number}</td>
                        <td>
                            <button class="btn btn-sm btn-primary add-test-detail" data-id="${form.id}">Add Test Detail</button>
                            <button class="btn btn-sm btn-info view-details" data-id="${form.id}">View Details</button>
                            <button class="btn btn-sm btn-warning edit-test-form" data-id="${form.id}">Edit</button>
                            <button class="btn btn-sm btn-danger delete-test-form" data-id="${form.id}">Delete</button>
                        </td>
                    </tr>
                `;
            });
            $('#testFormTableBody').html(html);
            $('#testFormModal').modal('show');
        });
    });

    // Handle View Details button click
    $(document).on('click', '.view-details', function() {
        const formId = $(this).attr('data-id');
        $.get(`${apiUrl}/test_forms/${formId}`, function(form) {
            let html = '';
            form.test_details.forEach(detail => {
                html += `
                    <tr>
                        <td>${detail.id}</td>
                        <td>${detail.test_name}</td>
                        <td>${detail.result}</td>
                        <td>
                            <button class="btn btn-sm btn-warning edit-test-detail" data-id="${detail.id}">Edit</button>
                            <button class="btn btn-sm btn-danger delete-test-detail" data-id="${detail.id}">Delete</button>
                        </td>
                    </tr>
                `;
            });
            $('#testDetailTableBody').html(html);
            $('#testDetailModal').modal('show');
        });
    });
});
