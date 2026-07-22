module full_adder_acc ( a, b, cin, cout, sum );
    input a;
    input b;
    input cin;
    output sum;
    output cout;
    wire  a_xor_b = a ^ b;
    wire  a_and_b = a & b;
    wire  a_and_cin = a & cin;
    wire  b_and_cin = b & cin;
    wire  _T_1 = a_and_b | b_and_cin;
    assign sum = a_xor_b ^ cin;
    assign cout = _T_1 | a_and_cin;
endmodule