$(document).ready(function() {
	//
	// Market Scanner for element43
	//
	// Scanning interval
	var interval = 3000;

	// Get Type IDs to scan for
	var table_ids = $('#scan_table tr[id]').map(function() {
		return this.id;
	}).get();

	// Get progressbar scaling
	var progress_step = 100 / table_ids.length;

	// Counter for iteration
	var i = 0;

	// Start scanning
	scan();

	// Iterate over all IDs


	function scan() {
		setTimeout(function() {
			if(i < table_ids.length) {

				// Show page in market browser
				CCPEVE.showMarketDetails(table_ids[i]);

				// Get slider value just to be sure
				interval = $("#slider").slider("value") * 1000;

				// Remove Row
				if(i !== 0) {
					$('#' + table_ids[i - 1]).children('td').animate({
						padding: 0
					}).wrapInner('<div />').children().slideUp(function() {
						$(this).closest('tr').remove();
					});
				}

				// Adjust progress bar
				$('#scan_progress').width(((i + 1) * progress_step) + "%");

				// Start pulsing
				$('#' + table_ids[i]).pulse({
					color: '#6EA8E5'
				}, {
					pulses: interval / 500
				});

				// Increase counter and call self
				i++;
				scan();
			} else {
				// When we're done remove last row, reload a fresh table and reinitialize page and finally start the scan process
				$('#' + table_ids[i - 1]).children('td').animate({
					padding: 0
				}).wrapInner('<div />').children().slideUp(function() {
					$(this).closest('tr').remove();
				});
				// Reload table
				$('#scan_table_container').slideUp();
				$('#scan_table_container').load(window.location.pathname + ' #scan_table', reinitialize());
			}
		}, interval);
	}

	function reinitialize() {
		$('#scan_table_container').slideDown();
		setTimeout(function() {
			// Reset Progress Bar
			$('#scan_progress').width("0%");

			// Get Type IDs to scan for
			table_ids = $('#scan_table tr[id]').map(function() {
				return this.id;
			}).get();

			// Get progressbar scaling
			progress_step = 100 / table_ids.length;

			// Counter for iteration
			i = 0;

			// Invoke scan process
			scan();
		}, 3000);
	}

	// Initialize slider
	$('#slider').slider({
		value: 3,
		min: 0.5,
		max: 5,
		step: 0.5,
		slide: function(event, ui) {

			// Get singular correct
			if(ui.value == 1) {
				$('#slider-label').html(ui.value + ' second per item');
			} else {
				$('#slider-label').html(ui.value + ' seconds per item');
			}

			// Show notice if speed is (too) fast
			if(ui.value < 3) {
				$('#speed-notice').show();
			} else {
				$('#speed-notice').hide();
			}

			interval = $("#slider").slider("value") * 1000;
		}
	});
	$('#speed-notice').hide();
	$("#slider-label").html($("#slider").slider("value") + ' seconds per item');

});