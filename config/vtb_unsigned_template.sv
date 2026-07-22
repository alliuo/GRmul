`timescale 1ns/1ps

module tb_unsigned;
    localparam int BW0 = {BW0};
    localparam int BW1 = {BW1};
    localparam int PW = BW0+BW1;
    localparam time APPLY_DELAY = 1;

    logic [BW0-1:0] a;
    logic [BW1-1:0] b;
    logic [PW-1:0]   product;
    logic [PW-1:0]   expected;

    {MUL_NAME} dut (
        .a(a),
        .b(b),
        .product(product)
    );

    logic [BW0-1:0] aval;
    logic [BW1-1:0] bval;
    logic [BW0-1:0] pair_a[$];
    logic [BW1-1:0] pair_b[$];
    
    int fp;
    string line;
    int r;
    longint unsigned temp_au;
    longint unsigned temp_bu;
    int errors = 0;
    int total  = 0;

    initial begin
        fp = $fopen("./input_combs.csv", "r");
        if (fp == 0) begin
            $display("ERROR: cannot open input_combs.csv");
            $finish;
        end

        while (!$feof(fp)) begin
            line = "";
            r = $fgets(line, fp);
            if (r == 0) break;

            if ($sscanf(line, "%d,%d", temp_au, temp_bu) == 2) begin
                aval = temp_au;
                bval = temp_bu;
                pair_a.push_back(aval);
                pair_b.push_back(bval);
            end else begin end
        end

        $fclose(fp);

        if (pair_a.size() == 0) begin
            $display("No valid pairs found in input_combs.csv -> exit");
            $finish;
        end

        $display("Read %0d unsigned pairs from input_combs.csv", pair_a.size());

        for (int i = 0; i < pair_a.size(); i++) begin
            total++;
            a = pair_a[i];
            b = pair_b[i];
            #APPLY_DELAY;
            
            expected = $unsigned(a) * $unsigned(b);

            if (product !== expected) begin
                errors++;
                $display("ERROR[%0d]: a=%0d, b=%0d => product=%0d, expected=%0d",
                         i, $unsigned(a), $unsigned(b), $unsigned(product), $unsigned(expected));
            end
        end

        if (errors == 0) begin
            $display("[PASS]: All %0d unsigned pairs matched.", total);
        end else begin
            $display("[FAIL]: %0d mismatches out of %0d unsigned pairs.", errors, total);
        end

        $finish;
    end

endmodule
