/////////////////////////////////////////////////////////////
// Created by: Synopsys DC Ultra(TM) in wire load mode
// Version   : T-2022.03-SP2
// Date      : Tue Jan 20 21:38:51 2026
/////////////////////////////////////////////////////////////


module AFA39 ( a, b, cin, cout, sum );
  input a, b, cin;
  output cout, sum;


  AOI21_X1 U5 ( .B1(b), .B2(a), .A(cin), .ZN(sum) );
  INV_X1 U6 ( .A(sum), .ZN(cout) );
endmodule

