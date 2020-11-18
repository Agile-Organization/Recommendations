$(function () {

    // ****************************************
    //  U T I L I T Y   F U N C T I O N S
    // ****************************************

    // Updates the form with data from the response
    function update_form_data(res) {
        $("#recommendation_product_id").val(res["product-id"]);
        $("#recommendation_related_product_id").val(res["related-product-id"]);
        $("#recommendation_type_id").val(res["type-id"]);
        if (res["status"] == true) {
            $("#recommendation_status").val("True");
        } else {
            $("#recommendation_status").val("False");
        }
    }

    /// Clears all form fields
    function clear_form_data() {
        $("#recommendation_product_id").val("");
        $("#recommendation_related_product_id").val("");
        $("#recommendation_type_id").val("");
        $("#recommendation_status").val("");
    }

    clear_form_data(); 

    // Updates the flash message area
    function flash_message(message) {
        $("#flash_message").empty();
        $("#flash_message").append(message);
    }

    // ****************************************
    // Create a Recommendation
    // ****************************************

    $("#create-btn").click(function () {

        var product_id = $("#recommendation_product_id").val();
        var related_product_id = $("#recommendation_related_product_id").val();
        var type_id = $("#recommendation_type_id").val();
        var status = $("#recommendation_status").val() == "True";

        if (!type_id){
            type_id = "1";
        }

        var data = {
            "product-id": parseInt(product_id, 10),
            "related-product-id": parseInt(related_product_id, 10),
            "type-id": parseInt(type_id, 10),
            "status": status
        };

        if (product_id && related_product_id){
            var ajax = $.ajax({
                type: "POST",
                url: "/recommendations/" + product_id + "/" + related_product_id,
                contentType: "application/json",
                data: JSON.stringify(data),
            });

            ajax.done(function(res){
                update_form_data(res)
                flash_message("Success")
            });

            ajax.fail(function(res){
                flash_message(res.responseJSON.message)
            });
        }
        else {
            flash_message("Please enter Product ID and Related Product ID")
        }
    });


    // ****************************************
    // Update a Recommendation
    // ****************************************

    $("#update-btn").click(function () {

        var product_id = $("#recommendation_product_id").val();
        var related_product_id = $("#recommendation_related_product_id").val();
        var type_id = $("#recommendation_type_id").val();
        var status = $("#recommendation_status").val() == "True";

        if (!type_id){
            type_id = "1";
        }

        var data = {
            "product-id": parseInt(product_id, 10),
            "related-product-id": parseInt(related_product_id, 10),
            "type-id": parseInt(type_id, 10),
            "status": status
        };

        if (product_id && related_product_id){
            var ajax = $.ajax({
                type: "PUT",
                url: "/recommendations/" + product_id + "/" + related_product_id,
                contentType: "application/json",
                data: JSON.stringify(data)
            })

            ajax.done(function(res){
                flash_message("Success")
            });

            ajax.fail(function(res){
                flash_message(res.responseJSON.message)
            });
        }
        else {
            flash_message("Please enter Product ID and Related Product ID")
        }

    });

    // ****************************************
    // Retrieve a Recommendation
    // ****************************************

    $("#retrieve-btn").click(function () {

        var product_id = $("#recommendation_product_id").val();
        var related_product_id = $("#recommendation_related_product_id").val();

        if (product_id && related_product_id){
            var ajax = $.ajax({
                type: "GET",
                url: "/recommendations/" + product_id + "/" + related_product_id,
                contentType: "application/json",
                data: ''
            })
    
            ajax.done(function(res){
                update_form_data(res)
                flash_message("Success")
            });
    
            ajax.fail(function(res){
                clear_form_data()
                flash_message(res.responseJSON.message)
            });
        }
        else{
            flash_message("Please enter Product ID and Related Product ID")
        }
    });

    // ****************************************
    // Delete a Recommendation
    // ****************************************

    $("#delete-btn").click(function () {

        var product_id = $("#recommendation_product_id").val();
        var related_product_id = $("#recommendation_related_product_id").val();

        if (product_id && related_product_id){
            var ajax = $.ajax({
                type: "DELETE",
                url: "/recommendations/" + product_id + "/" + related_product_id,
                contentType: "application/json",
                data: '',
            })
    
            ajax.done(function(res){
                clear_form_data()
                flash_message("Recommendation has been Deleted!")
            });
    
            ajax.fail(function(res){
                flash_message("Server error!")
            });
        }
        else {
            flash_message("Please enter Product ID and Related Product ID")
        }
    });

    // ****************************************
    // Clear the form
    // ****************************************

    $("#clear-btn").click(function () {
        clear_form_data()
    });

    // ****************************************
    // Search for a Recommendation
    // ****************************************

    $("#search-btn").click(function () {

        var product_id = $("#recommendation_product_id").val();
        var related_product_id = $("#recommendation_related_product_id").val();
        var type_id = $("#recommendation_type_id").val();
        var status = $("#recommendation_status").val();

        var queryString = ""

        if (product_id) {
            queryString += 'product-id=' + product_id
        }
        if (related_product_id) {
            if (queryString.length > 0) {
                queryString += '&related-product-id=' + related_product_id
            } else {
                queryString += 'related-product-id=' + category
            }
        }
        if (type_id) {
            if (queryString.length > 0) {
                queryString += '&type-id=' + type_id
            } else {
                queryString += 'type-id=' + type_id
            }
        }
        if (status) {
            if (queryString.length > 0) {
                queryString += '&status=' + status
            } else {
                queryString += 'status=' + status
            }
        }

        var ajax = $.ajax({
            type: "GET",
            url: "/recommendations?" + queryString,
            contentType: "application/json",
            data: ''
        })

        ajax.done(function(res){
            //alert(res.toSource())
            console.log(res)
            $("#search_results").empty();
            $("#search_results").append('<table class="table-striped" cellpadding="10">');
            var header = '<tr>'
            header += '<th style="width:10%">Product ID</th>'
            header += '<th style="width:40%">Related Product ID</th>'
            header += '<th style="width:40%">Type ID</th>'
            header += '<th style="width:10%">Active Status</th></tr>'
            $("#search_results").append(header);
            var firstRecommendation = "";
            for(var i = 0; i < res.length; i++) {
                var recommendation = res[i];
                var row = "<tr><td>"+recommendation["product-id"]+"</td><td>"+recommendation["related-product-id"]+"</td><td>"+recommendation["type-id"]+"</td><td>"+recommendation["status"]+"</td></tr>";
                $("#search_results").append(row);
                if (i == 0) {
                    firstRecommendation = recommendation;
                }
            }

            $("#search_results").append('</table>');

            // copy the first result to the form
            if (firstRecommendation != "") {
                update_form_data(firstRecommendation)
            }

            flash_message("Success")
        });

        ajax.fail(function(res){
            flash_message(res.responseJSON.message)
        });

    });

    // ****************************************
    // Toggle the status of a recommendation
    // ****************************************

    $("#toggle-btn").click(function () {

        var product_id = $("#recommendation_product_id").val();
        var related_product_id = $("#recommendation_related_product_id").val();

        if (product_id && related_product_id){
            var ajax = $.ajax({
                type: "PUT",
                url: "/recommendations/" + product_id + "/" + related_product_id + "/toggle"
            })

            ajax.done(function(res){
                flash_message("Success");
                update_form_data(res);
            });

            ajax.fail(function(res){
                flash_message(res.responseJSON.message)
            });
        }
        else {
            flash_message("Please enter Product ID and Related Product ID")
        }

    });

})
