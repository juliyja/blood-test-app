$(function () {
    $(".date-picker").each(function () {
        if ($(this).hasClass("dob")) {
            $(this).datepicker({
                    changeMonth: true,
                    changeYear: true,
                    dateFormat: "dd-mm-yy",
                    maxDate: new Date(),
                    yearRange: "-120:+20"
                }
            );
        } else {
            $(this).datepicker({
                    changeMonth: true,
                    changeYear: true,
                    dateFormat: "dd-mm-yy",
                    yearRange: "-120:+20"
                }
            );
        }

    });

});