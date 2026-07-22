`timescale 1ns/1ps

module tb_signed;
    localparam int BW0 = {BW0};
    localparam int BW1 = {BW1};
    localparam int PW = BW0+BW1;
    localparam time APPLY_DELAY = 1;

    logic signed [BW0-1:0] a;
    logic signed [BW1-1:0] b;
    logic signed [PW-1:0]   product;
    logic signed [PW-1:0]   expected;

    {MUL_NAME} dut (
        .a(a),
        .b(b),
        .product(product)
    );

    logic signed [BW0-1:0] aval;
    logic signed [BW1-1:0] bval;
    logic signed [BW0-1:0] pair_a[$];
    logic signed [BW1-1:0] pair_b[$];

    int fp;
    string line;
    int r;
    longint temp_as; // signed temporary
    longint temp_bs;
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

            if ($sscanf(line, "%d,%d", temp_as, temp_bs) == 2) begin
                aval = temp_as;
                bval = temp_bs;
                pair_a.push_back(aval);
                pair_b.push_back(bval);
            end else begin end
        end

        $fclose(fp);

        if (pair_a.size() == 0) begin
            $display("No valid pairs found in input_combs.csv -> exit");
            $finish;
        end

        $display("Read %0d signed pairs from input_combs.csv", pair_a.size());

        for (int i = 0; i < pair_a.size(); i++) begin
            total++;
            a = pair_a[i];
            b = pair_b[i];
            #APPLY_DELAY;

            expected = $signed(a) * $signed(b);

            if (product !== expected) begin
                errors++;
                $display("ERROR[%0d]: a=%0d, b=%0d => product=%0d, expected=%0d",
                         i, $signed(a), $signed(b), $signed(product), $signed(expected));
            end
        end

        if (errors == 0) begin
            $display("[PASS]: All %0d signed pairs matched.", total);
        end else begin
            $display("[FAIL]: %0d mismatches out of %0d signed pairs.", errors, total);
        end

        $finish;
    end

endmodule
