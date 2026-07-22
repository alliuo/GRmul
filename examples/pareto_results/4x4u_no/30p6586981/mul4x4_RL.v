// Area: 68.5, Delay: 0.4693
module mul4x4_RL (
    input  wire [3:0]  a,
    input  wire [3:0]  b,
    output wire [7:0] product
);
    wire a0_b0;
    assign a0_b0 = a[0] & b[0];
    wire a0_b1;
    assign a0_b1 = a[0] & b[1];
    wire a0_b2;
    assign a0_b2 = a[0] & b[2];
    wire a0_b3;
    assign a0_b3 = a[0] & b[3];
    wire a1_b0;
    assign a1_b0 = a[1] & b[0];
    wire a1_b1;
    assign a1_b1 = a[1] & b[1];
    wire a1_b2;
    assign a1_b2 = a[1] & b[2];
    wire a1_b3;
    assign a1_b3 = a[1] & b[3];
    wire a2_b0;
    assign a2_b0 = a[2] & b[0];
    wire a2_b1;
    assign a2_b1 = a[2] & b[1];
    wire a2_b2;
    assign a2_b2 = a[2] & b[2];
    wire a2_b3;
    assign a2_b3 = a[2] & b[3];
    wire a3_b0;
    assign a3_b0 = a[3] & b[0];
    wire a3_b1;
    assign a3_b1 = a[3] & b[1];
    wire a3_b2;
    assign a3_b2 = a[3] & b[2];
    wire a3_b3;
    assign a3_b3 = a[3] & b[3];
    
    assign product[0] = a0_b0;
    wire pp_1;
    wire pp_2;
    wire pp_3;
    wire pp_5;
    wire pp_6;
    wire pp_7;
    wire pp_8;
    wire pp_9;
    wire pp_11;
    wire pp_12;
    wire pp_13;
    wire pp_14;
    wire pp_15;
    wire pp_17;
    wire pp_18;
    wire pp_19;
    wire pp_21;
    wire pp_22;
    wire pp_23;
    wire pp_25;
    
    full_adder_acc fa_0 (.a(pp_2), .b(a1_b1), .cin(a2_b0), .sum(product[2]), .cout(pp_5));
    full_adder_acc fa_1 (.a(a1_b2), .b(a0_b3), .cin(a2_b1), .sum(pp_6), .cout(pp_7));
    full_adder_acc fa_2 (.a(pp_6), .b(pp_3), .cin(a3_b0), .sum(pp_8), .cout(pp_9));
    full_adder_acc fa_3 (.a(pp_7), .b(pp_12), .cin(a1_b3), .sum(pp_14), .cout(pp_15));
    AFA0 fa_4 (.a(pp_9), .b(pp_14), .cin(pp_11), .sum(product[4]), .cout(pp_17));
    AFA6 fa_5 (.a(a2_b3), .b(pp_13), .cin(a3_b2), .sum(pp_18), .cout(pp_19));
    full_adder_acc fa_6 (.a(pp_17), .b(pp_18), .cin(pp_15), .sum(product[5]), .cout(pp_21));
    
    half_adder ha_0 (.a(a0_b1), .b(a1_b0), .sum(product[1]), .cout(pp_1));
    half_adder ha_1 (.a(a0_b2), .b(pp_1), .sum(pp_2), .cout(pp_3));
    half_adder ha_5 (.a(pp_5), .b(pp_8), .sum(product[3]), .cout(pp_11));
    half_adder ha_6 (.a(a3_b1), .b(a2_b2), .sum(pp_12), .cout(pp_13));
    half_adder ha_11 (.a(a3_b3), .b(pp_19), .sum(pp_22), .cout(pp_23));
    half_adder ha_12 (.a(pp_22), .b(pp_21), .sum(product[6]), .cout(pp_25));
    AHA1 ha_13 (.a(pp_25), .b(pp_23), .sum(product[7]), .cout());
endmodule