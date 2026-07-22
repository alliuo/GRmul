/////////////////////////////////////////////////////////////
// Created by: Synopsys DC Ultra(TM) in wire load mode
// Version   : T-2022.03-SP2
// Date      : Tue Jan 20 21:51:13 2026
/////////////////////////////////////////////////////////////


module AFA49 ( a, b, cin, cout, sum );
  input a, b, cin;
  output cout, sum;

  assign sum = 1'b0;

  OR2_X1 U5 ( .A1(cin), .A2(a), .ZN(cout) );
endmodule

