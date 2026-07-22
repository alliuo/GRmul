/////////////////////////////////////////////////////////////
// Created by: Synopsys DC Ultra(TM) in wire load mode
// Version   : T-2022.03-SP2
// Date      : Tue Jan 20 21:16:44 2026
/////////////////////////////////////////////////////////////


module AFA21 ( a, b, cin, cout, sum );
  input a, b, cin;
  output cout, sum;


  AND2_X1 U5 ( .A1(b), .A2(a), .ZN(cout) );
  XOR2_X1 U6 ( .A(b), .B(a), .Z(sum) );
endmodule

