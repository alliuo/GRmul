/////////////////////////////////////////////////////////////
// Created by: Synopsys DC Ultra(TM) in wire load mode
// Version   : T-2022.03-SP2
// Date      : Tue Jan 20 21:47:30 2026
/////////////////////////////////////////////////////////////


module AFA46 ( a, b, cin, cout, sum );
  input a, b, cin;
  output cout, sum;

  assign cout = 1'b1;

  AND2_X1 U5 ( .A1(cin), .A2(b), .ZN(sum) );
endmodule

