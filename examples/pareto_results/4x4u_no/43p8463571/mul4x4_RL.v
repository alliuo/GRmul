// Area: 69.0, Delay: 0.4013
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
    
    full_adder_acc fa_0 (.a(a2_b0), .b(a1_b1), .cin(a0_b2), .sum(pp_2), .cout(pp_3));
    full_adder_acc fa_1 (.a(a0_b3), .b(a3_b0), .cin(a1_b2), .sum(pp_6), .cout(pp_7));
    AFA2 fa_2 (.a(pp_5), .b(pp_8), .cin(pp_6), .sum(product[3]), .cout(pp_11));
    full_adder_acc fa_3 (.a(a2_b2), .b(a3_b1), .cin(a1_b3), .sum(pp_12), .cout(pp_13));
    full_adder_acc fa_4 (.a(pp_12), .b(pp_9), .cin(pp_7), .sum(pp_14), .cout(pp_15));
    full_adder_acc fa_5 (.a(pp_13), .b(a2_b3), .cin(a3_b2), .sum(pp_18), .cout(pp_19));
    AFA1 fa_6 (.a(pp_15), .b(pp_17), .cin(pp_18), .sum(product[5]), .cout(pp_21));
    AFA1 fa_7 (.a(pp_19), .b(pp_21), .cin(a3_b3), .sum(product[6]), .cout(product[7]));
    
    half_adder ha_0 (.a(a0_b1), .b(a1_b0), .sum(product[1]), .cout(pp_1));
    half_adder ha_2 (.a(pp_1), .b(pp_2), .sum(product[2]), .cout(pp_5));
    half_adder ha_4 (.a(a2_b1), .b(pp_3), .sum(pp_8), .cout(pp_9));
    half_adder ha_8 (.a(pp_14), .b(pp_11), .sum(product[4]), .cout(pp_17));
endmodule