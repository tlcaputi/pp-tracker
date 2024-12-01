
options(echo = FALSE)
if(!require("pacman")) install.packages("pacman")
pacman::p_load(logger, glue, dplyr, tidyverse, lubridate)

# Go through and process all csv files in the output-pp-selenium directory
csv_files = rev(list.files("output-pp-selenium", pattern=".csv", full.names=TRUE))

# for(idx in seq_along(csv_files)) {
for(idx in 1:length(csv_files)) {

    csv_file = csv_files[idx]

    log_info("Processing {csv_file}")

    multiplierfn = gsub(".csv", ".pdf", csv_file)
    productfn = gsub(".csv", "-product.pdf", csv_file)
    current_multiplier_fn = "current-multiplier.pdf"
    current_product_fn = "current-product.pdf"

    # Read in data
    df = read_csv(csv_file)

    # Only take unique observations
    df = df %>% 
        distinct()

    
    # Define variables        
    df = df %>%
        mutate(
            min_multiplier = pmin(multiplier1, multiplier2),
            neg_min_multiplier = -min_multiplier,
            product = multiplier1 * multiplier2
        ) 

    # Put a linebreak in the middle of text
    df = df %>% 
        mutate(
            text_nchar = nchar(text),
            half_text_nchar = round(text_nchar / 2),
            text = glue("{substr(text, 1, half_text_nchar)}\n{substr(text, half_text_nchar + 1, text_nchar)}"),
        )

    # When the data is correctly parsed, we can create a better text field
    try({
        df = df %>%
            mutate(
                text = glue("{player_name} {number} {stat}\n{game}-{game_time} ({multiplier1} x {multiplier2} = {product})\n{timestamp}")
            )
    })

    # Remove college games, which I can't bet on
    try({
        df = df %>%
            filter(
                !(trimws(type_a) %in% c("CFB", "NCAA", "CBB", "NCAAF"))
            )

    })

    # Remove games without a game or game_time
    log_info("Removing games without a game or game_time")
    df = df %>%
        filter(
            !is.na(game), !is.na(game_time), !is.na(timestamp), !is.na(multiplier1), !is.na(multiplier2), !is.na(product), !is.na(min_multiplier),
            is.finite(multiplier1), is.finite(multiplier2), is.finite(product), is.finite(min_multiplier)
        )

    df %>% tail(10) %>% as.data.frame() %>% print()
    # exit()

        
    # Figure out ranking of min_multiplier for each timestamp
    df = df %>% 
        group_by(timestamp) %>% 
        mutate(
            neg_min_multiplier_rank = dense_rank(neg_min_multiplier)
        ) %>% 
        ungroup() 
        
    # For each timestamp, only take the two largest min_multipliers
    df = df %>% 
        arrange(timestamp, neg_min_multiplier_rank, desc(product)) 
        
    # Only want one observation per game
    log_info("Only want one observation per game")
    try({
        df = df %>%
            group_by(timestamp, game, game_time) %>% 
            slice_head(n=1) %>% 
            ungroup() 
    })
    log_info("nrow(df): {nrow(df)}")

    # df %>%
    #     head(30) %>%
    #     as.data.frame() %>%
    #     print()


    df = df %>%
            arrange(timestamp, neg_min_multiplier_rank, desc(product))


    # Only take the two largest min_multipliers for each timestamp
    log_info("Only take the two largest min_multipliers for each timestamp")
    df = df %>% 
        group_by(timestamp) %>% 
        slice_head(n=2) %>%
        mutate(
            row = row_number(),
        ) %>% 
        ungroup() 
    log_info("nrow(df): {nrow(df)}")



    tmp = df %>% 
        group_by(timestamp) %>% 
        mutate(
            min_multiplier_1 = first(min_multiplier[row == 1]),
            min_multiplier_2 = first(min_multiplier[row == 2])
        ) %>%
        ungroup() 



    # Rename min_multiplier = -neg_min_multiplier
    df = df %>% 
        mutate(
            row_str = case_when(row == 1 ~ "1st Best Bet", row == 2 ~ "2nd Bet Bet"),
            min_multiplier = -neg_min_multiplier,
        )

    # Only take timestamps where the min multiplier is at least 1.81 for both the 
    # first and second bet. Anything else is likely to be an error.
    df = df %>% 
        group_by(timestamp) %>%
        mutate(
            min_min_multiplier = min(min_multiplier, na.rm = T),
        ) %>% 
        ungroup() %>% 
        filter(
            min_min_multiplier > 1.70
        )

    MAX_MULTIPLIER = max(df$min_multiplier, na.rm = T)
    MIN_MULTIPLIER = min(df$min_multiplier, na.rm = T)
    MAX_PRODUCT = max(df$product, na.rm = T)
    MIN_PRODUCT = min(df$product, na.rm = T)
    MAX_MULTIPLIER_SCALE = max(MAX_MULTIPLIER - MIN_MULTIPLIER, 0.1) / 5
    MAX_PRODUCT_SCALE = max(MAX_PRODUCT - MIN_PRODUCT, 0.1) / 5

    log_info("Max Multiplier: {MAX_MULTIPLIER}")
    log_info("Min Multiplier: {MIN_MULTIPLIER}")
    log_info("Max Product: {MAX_PRODUCT}")
    log_info("Min Product: {MIN_PRODUCT}")
    log_info("Max Multiplier Scale: {MAX_MULTIPLIER_SCALE}")
    log_info("Max Product Scale: {MAX_PRODUCT_SCALE}")


    # Extract last timestamps
    log_info("Extract last timestamps")
    log_info("nrow(df): {nrow(df)}")
    last_timestamps = df %>% 
        arrange(desc(timestamp)) %>% 
        head(2) %>% 
        transmute(
            row_str,
            row = as.numeric(row),
            min_multiplier,
            timestamp,
            product,
            text,
            max_product = max(product, na.rm = T),
            min_product = min(product, na.rm = T),
            max_min_multiplier = max(min_multiplier, na.rm = T),
            min_min_multiplier = min(min_multiplier, na.rm = T),
            product_1 = first(product[row == 1]),
            product_2 = first(product[row == 2]),
            multiplier_1 = first(min_multiplier[row == 1]),
            multiplier_2 = first(min_multiplier[row == 2]),
            other_product = case_when(
                row == 1 ~ product_2,
                row == 2 ~ product_1
            ),
            other_multiplier = case_when(
                row == 1 ~ multiplier_2,
                row == 2 ~ multiplier_1
            ),
        ) %>% 
        mutate(
            product_text_y = case_when(
                abs(max_product - min_product) < (2*MAX_PRODUCT_SCALE) ~ if_else(product == max_product, product + MAX_PRODUCT_SCALE, product - MAX_PRODUCT_SCALE),
                T ~ product
            ),
            min_multiplier_text_y = case_when(
                max_min_multiplier == min_min_multiplier ~ if_else(row == 1, min_multiplier + MAX_MULTIPLIER_SCALE, min_multiplier - MAX_MULTIPLIER_SCALE),
                T ~ min_multiplier
            ),
            product_text_y = case_when(
                abs(product - other_product) < (2*MAX_PRODUCT_SCALE) ~ if_else(row == 1, product + MAX_PRODUCT_SCALE, product - MAX_PRODUCT_SCALE),
                T ~ product
            ),
            min_multiplier_text_y = case_when(
                abs(min_multiplier - other_multiplier) < (2*MAX_MULTIPLIER_SCALE) ~ if_else(row == 1, min_multiplier + MAX_MULTIPLIER_SCALE, min_multiplier - MAX_MULTIPLIER_SCALE),
                T ~ min_multiplier
            ),
        )


    log_info("head(df)")
    df %>% head(10) %>% as.data.frame() %>% print()
    log_info("Last timestamps")
    last_timestamps %>% as.data.frame() %>% print()
    # exit()

    ## MIN MULTIPLIER PLOT
    # Plot two lines, one for the two largest min_multipliers by timestamp
    p = ggplot(df, aes(x=timestamp, y=min_multiplier, color=row_str)) +
        geom_point() +
        geom_line() +
        labs(
            title = "PP Max Min Multiplier",
            subtitle = "Choose when the two min multipliers are the largest",
            x="Timestamp",
            y="Min Multiplier",
            color = "Bet"
        ) +
        theme_minimal()

    # Add text for the two last timestamps
    p = p + 
        geom_text(
            data=last_timestamps,
            aes(
                x=timestamp,
                y=min_multiplier_text_y,
                label=text
            ),
            hjust=0.001,
            vjust=0,
            lineheight=0.8
        )
    

    # Extend plot horizontally so that text is visible
    p = p + 
        scale_x_datetime(
            expand=c(0.01, 0.01),
            limits=c(min(df$timestamp, na.rm = T), max(df$timestamp, na.rm = T) + hours(12))
        )
    
    # Extent plot vertically so that text is visible
    p = p + 
        scale_y_continuous(
            expand=c(0.01, 0.01),
            limits=c(MIN_MULTIPLIER - (MAX_MULTIPLIER_SCALE*2), MAX_MULTIPLIER + (MAX_MULTIPLIER_SCALE*2))
        )

    # Save plot
    ggsave(multiplierfn, p, width = 10, height = 5)
    log_info("Saved {multiplierfn}")

    if(idx == 1){
        # Save the current multiplier plot
        ggsave(current_multiplier_fn, p, width = 10, height = 5)
        log_info("Saved {current_multiplier_fn}")
    }


    ## PRODUCT PLOT

    # Plot two lines, one for the two largest min_multipliers by timestamp
    p = ggplot(df, aes(x = timestamp, y = product, color = row_str)) +
        geom_point() +
        geom_line() +
        labs(
            title = "PP Max Min Multiplier",
            subtitle = "Choose when the two min multipliers are the largest",
            x = "Timestamp",
            y = "Product",
            color = "Bet"
        ) +
        theme_minimal()

    # Add text for the two last timestamps
    p = p +
        geom_text(
            data = last_timestamps,
            aes(
                x = timestamp,
                y = product_text_y,
                label = text
            ),
            hjust = 0.001,
            vjust = 0,
            lineheight = 0.8
        )


    # Extend plot horizontally so that text is visible
    p = p +
        scale_x_datetime(
            expand = c(0.01, 0.01),
            limits = c(min(df$timestamp, na.rm = T), max(df$timestamp, na.rm = T) + hours(12))
        )

    # Extent plot vertically so that text is visible
    p = p +
        scale_y_continuous(
            expand = c(0.01, 0.01),
            limits = c(MIN_PRODUCT - (MAX_PRODUCT_SCALE * 2), MAX_PRODUCT + (MAX_PRODUCT_SCALE * 2))
        )

    # Save plot
    ggsave(productfn, p, width = 10, height = 5)
    log_info("Saved {productfn}")

    if(idx == 1){
        # Save the current product plot
        ggsave(current_product_fn, p, width = 10, height = 5)
        log_info("Saved {current_product_fn}")
    }


}