// Area: 99.5, Delay: 0.46585
module mul4x4_RL (
    input  wire [3:0]  a,
    input  wire [3:0]  b,
    output wire [7:0] product
);
    wire [1:0] one, two, neg;
    assign one[0] = b[0];
    assign two[0] = b[1] & ~b[0];
    assign neg[0] = b[1];
    assign one[1] = b[2] ^ b[1];
    assign two[1] = (~b[3] & b[2] & b[1]) | (b[3] & ~b[2] & ~b[1]);
    assign neg[1] = b[3] & ~(b[2] & b[1]);
    
    wire [4:0] ext_a, a2;
    assign ext_a = {1'b0, a};
    assign a2 = {a, 1'b0};    
    wire [4:0] booth0;
    assign booth0 = (({5{one[0]}} & ext_a) | ({5{two[0]}} & a2)) ^ {5{neg[0]}};
    wire [4:0] booth1;
    assign booth1 = (({5{one[1]}} & ext_a) | ({5{two[1]}} & a2)) ^ {5{neg[1]}};
    wire [3:0] booth2;
    assign booth2 = ({4{b[3]}} & a);
    
    wire [1:0] sign_ext;
    assign sign_ext = neg;
    
    wire constant1_5;
    assign constant1_5 = 1'b1;
    wire constant1_6;
    assign constant1_6 = 1'b1;
    wire pp_1;
    wire pp_3;
    wire pp_4;
    wire pp_5;
    wire pp_7;
    wire pp_8;
    wire pp_9;
    wire pp_11;
    wire pp_12;
    wire pp_13;
    wire pp_15;
    wire pp_16;
    wire pp_17;
    wire pp_18;
    wire pp_19;
    wire pp_21;
    wire pp_22;
    wire pp_23;
    wire pp_24;
    wire pp_25;
    wire pp_27;
    wire pp_28;
    wire pp_29;
    
    full_adder_acc fa_0 (.a(booth1[0]), .b(booth0[2]), .cin(neg[1]), .sum(pp_4), .cout(pp_5));
    full_adder_acc fa_1 (.a(pp_7), .b(pp_5), .cin(pp_8), .sum(product[3]), .cout(pp_11));
    full_adder_acc fa_2 (.a(booth1[2]), .b(booth2[0]), .cin(booth0[4]), .sum(pp_12), .cout(pp_13));
    full_adder_acc fa_3 (.a(pp_11), .b(pp_9), .cin(pp_12), .sum(product[4]), .cout(pp_15));
    AFA26 fa_4 (.a(booth1[3]), .b(booth2[1]), .cin(constant1_5), .sum(pp_16), .cout(pp_17));
    full_adder_acc fa_5 (.a(pp_15), .b(pp_18), .cin(pp_13), .sum(product[5]), .cout(pp_21));
    AFA26 fa_6 (.a(booth1[4]), .b(booth2[2]), .cin(constant1_6), .sum(pp_22), .cout(pp_23));
    full_adder_acc fa_7 (.a(pp_19), .b(pp_22), .cin(pp_17), .sum(pp_24), .cout(pp_25));
    full_adder_acc fa_8 (.a(pp_25), .b(pp_28), .cin(pp_23), .sum(pp_29), .cout());
    
    half_adder ha_0 (.a(neg[0]), .b(booth0[0]), .sum(product[0]), .cout(pp_1));
    half_adder ha_1 (.a(booth0[1]), .b(pp_1), .sum(product[1]), .cout(pp_3));
    half_adder ha_3 (.a(pp_3), .b(pp_4), .sum(product[2]), .cout(pp_7));
    half_adder ha_4 (.a(booth1[1]), .b(booth0[3]), .sum(pp_8), .cout(pp_9));
    half_adder ha_9 (.a(~sign_ext[0]), .b(pp_16), .sum(pp_18), .cout(pp_19));
    half_adder ha_13 (.a(pp_24), .b(pp_21), .sum(product[6]), .cout(pp_27));
    half_adder ha_14 (.a(~sign_ext[1]), .b(booth2[3]), .sum(pp_28), .cout());
    half_adder ha_16 (.a(pp_29), .b(pp_27), .sum(product[7]), .cout());
endmodule