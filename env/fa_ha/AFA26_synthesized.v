/////////////////////////////////////////////////////////////
// Created by: Synopsys DC Ultra(TM) in wire load mode
// Version   : T-2022.03-SP2
// Date      : Tue Jan 20 21:22:54 2026
/////////////////////////////////////////////////////////////


module AFA26 ( a, b, cin, cout, sum );
  input a, b, cin;
  output cout, sum;


  OR2_X1 U5 ( .A1(a), .A2(b), .ZN(cout) );
  XNOR2_X1 U6 ( .A(a), .B(b), .ZN(sum) );
endmodule

