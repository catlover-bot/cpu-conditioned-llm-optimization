; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_gramschmidt(i32 noundef %m, i32 noundef %n, ptr noundef %A, ptr noundef %R, ptr noundef %Q) #0 {
entry:
  %cmp.n = icmp sgt i32 %n, 0
  br i1 %cmp.n, label %n.check, label %for.end94

n.check:
  %cmp.m = icmp sgt i32 %m, 0
  %n64 = sext i32 %n to i64
  %m64 = sext i32 %m to i64
  br label %for.cond

for.cond:                                         ; preds = %for.inc92, %n.check
  %k = phi i32 [ 0, %n.check ], [ %inc93, %for.inc92 ]
  %k64 = sext i32 %k to i64
  br i1 %cmp.m, label %for.body.preheader, label %for.end.skip

for.body.preheader:
  br label %for.body8

for.body8:                                         ; preds = %for.body8, %for.body.preheader
  %i.06 = phi i32 [ 0, %for.body.preheader ], [ %inc, %for.body8 ]
  %nrm.05 = phi double [ 0.000000e+00, %for.body.preheader ], [ %add15, %for.body8 ]
  %i64.06 = sext i32 %i.06 to i64
  %rowoff = mul nsw i64 %i64.06, %n64
  %elemptr = getelementptr inbounds double, ptr %A, i64 %rowoff
  %elemptr2 = getelementptr inbounds double, ptr %elemptr, i64 %k64
  %aval = load double, ptr %elemptr2, align 8
  %mul = fmul double %aval, %aval
  %add15 = fadd double %nrm.05, %mul
  %inc = add nsw i32 %i.06, 1
  %cmp7 = icmp slt i32 %inc, %m
  br i1 %cmp7, label %for.body8, label %for.end.loopexit

for.end.loopexit:
  %nrm.lcssa = phi double [ %add15, %for.body8 ]
  br label %for.end

for.end.skip:
  br label %for.end

for.end:                                           ; preds = %for.end.loopexit, %for.end.skip
  %nrm.final = phi double [ %nrm.lcssa, %for.end.loopexit ], [ 0.000000e+00, %for.end.skip ]
  %call = call double @sqrt(double noundef %nrm.final) #2
  %Rk_rowoff = mul nsw i64 %k64, %n64
  %Rk_row = getelementptr inbounds double, ptr %R, i64 %Rk_rowoff
  %Rkk_ptr = getelementptr inbounds double, ptr %Rk_row, i64 %k64
  store double %call, ptr %Rkk_ptr, align 8

  br i1 %cmp.m, label %for.body22.preheader, label %for.end37

for.body22.preheader:
  br label %for.body22

for.body22:                                        ; preds = %for.body22, %for.body22.preheader
  %i2.06 = phi i32 [ 0, %for.body22.preheader ], [ %inc36, %for.body22 ]
  %i2_64 = sext i32 %i2.06 to i64
  %A_rowoff2 = mul nsw i64 %i2_64, %n64
  %A_row2 = getelementptr inbounds double, ptr %A, i64 %A_rowoff2
  %A_elem2 = getelementptr inbounds double, ptr %A_row2, i64 %k64
  %aval2 = load double, ptr %A_elem2, align 8
  %rkk_val = load double, ptr %Rkk_ptr, align 8
  %div = fdiv double %aval2, %rkk_val
  %Q_rowoff = mul nsw i64 %i2_64, %n64
  %Q_row = getelementptr inbounds double, ptr %Q, i64 %Q_rowoff
  %Q_elem = getelementptr inbounds double, ptr %Q_row, i64 %k64
  store double %div, ptr %Q_elem, align 8
  %inc36 = add nsw i32 %i2.06, 1
  %cmp21 = icmp slt i32 %inc36, %m
  br i1 %cmp21, label %for.body22, label %for.end37.loopexit

for.end37.loopexit:
  br label %for.end37

for.end37:                                         ; preds = %for.end37.loopexit, %for.end
  %j.init = add nsw i32 %k, 1
  %cmp.j = icmp slt i32 %j.init, %n
  br i1 %cmp.j, label %for.cond39.preheader, label %for.end91

for.cond39.preheader:
  br label %for.cond39

for.cond39:                                        ; preds = %for.inc89, %for.cond39.preheader
  %j = phi i32 [ %j.init, %for.cond39.preheader ], [ %inc90, %for.inc89 ]
  %j64 = sext i32 %j to i64
  %Rk_row.2 = getelementptr inbounds double, ptr %R, i64 %Rk_rowoff
  %Rkj_ptr = getelementptr inbounds double, ptr %Rk_row.2, i64 %j64
  store double 0.000000e+00, ptr %Rkj_ptr, align 8

  br i1 %cmp.m, label %for.body48.preheader, label %for.end65

for.body48.preheader:
  br label %for.body48

for.body48:                                        ; preds = %for.body48, %for.body48.preheader
  %i3.06 = phi i32 [ 0, %for.body48.preheader ], [ %inc64, %for.body48 ]
  %i3_64 = sext i32 %i3.06 to i64
  %Q_rowoff3 = mul nsw i64 %i3_64, %n64
  %Q_row3 = getelementptr inbounds double, ptr %Q, i64 %Q_rowoff3
  %Q_elem3 = getelementptr inbounds double, ptr %Q_row3, i64 %k64
  %qval = load double, ptr %Q_elem3, align 8
  %A_rowoff3 = mul nsw i64 %i3_64, %n64
  %A_row3 = getelementptr inbounds double, ptr %A, i64 %A_rowoff3
  %A_elem3 = getelementptr inbounds double, ptr %A_row3, i64 %j64
  %aval3 = load double, ptr %A_elem3, align 8
  %mul57 = fmul double %qval, %aval3
  %rkj_cur = load double, ptr %Rkj_ptr, align 8
  %add62 = fadd double %rkj_cur, %mul57
  store double %add62, ptr %Rkj_ptr, align 8
  %inc64 = add nsw i32 %i3.06, 1
  %cmp47 = icmp slt i32 %inc64, %m
  br i1 %cmp47, label %for.body48, label %for.end65.loopexit

for.end65.loopexit:
  br label %for.end65

for.end65:                                         ; preds = %for.end65.loopexit, %for.cond39
  br i1 %cmp.m, label %for.body68.preheader, label %for.end88

for.body68.preheader:
  br label %for.body68

for.body68:                                        ; preds = %for.body68, %for.body68.preheader
  %i4.06 = phi i32 [ 0, %for.body68.preheader ], [ %inc87, %for.body68 ]
  %i4_64 = sext i32 %i4.06 to i64
  %A_rowoff4 = mul nsw i64 %i4_64, %n64
  %A_row4 = getelementptr inbounds double, ptr %A, i64 %A_rowoff4
  %A_elem4j = getelementptr inbounds double, ptr %A_row4, i64 %j64
  %aval4 = load double, ptr %A_elem4j, align 8
  %Q_rowoff4 = mul nsw i64 %i4_64, %n64
  %Q_row4 = getelementptr inbounds double, ptr %Q, i64 %Q_rowoff4
  %Q_elem4k = getelementptr inbounds double, ptr %Q_row4, i64 %k64
  %qval4 = load double, ptr %Q_elem4k, align 8
  %rkj_final = load double, ptr %Rkj_ptr, align 8
  %mul81 = fmul double %qval4, %rkj_final
  %sub = fsub double %aval4, %mul81
  store double %sub, ptr %A_elem4j, align 8
  %inc87 = add nsw i32 %i4.06, 1
  %cmp67 = icmp slt i32 %inc87, %m
  br i1 %cmp67, label %for.body68, label %for.end88.loopexit

for.end88.loopexit:
  br label %for.end88

for.end88:                                         ; preds = %for.end88.loopexit, %for.end65
  br label %for.inc89

for.inc89:                                         ; preds = %for.end88
  %inc90 = add nsw i32 %j, 1
  %cmp.j.next = icmp slt i32 %inc90, %n
  br i1 %cmp.j.next, label %for.cond39, label %for.end91.loopexit

for.end91.loopexit:
  br label %for.end91

for.end91:                                         ; preds = %for.end91.loopexit, %for.end37
  br label %for.inc92

for.inc92:                                         ; preds = %for.end91
  %inc93 = add nsw i32 %k, 1
  %cmp.k.next = icmp slt i32 %inc93, %n
  br i1 %cmp.k.next, label %for.cond, label %for.end94.loopexit

for.end94.loopexit:
  br label %for.end94

for.end94:                                         ; preds = %for.end94.loopexit, %entry
  ret void
}

; Function Attrs: nounwind
declare double @sqrt(double noundef) #1

attributes #0 = { noinline nounwind uwtable "frame-pointer"="all" "min-legal-vector-width"="0" "no-trapping-math"="true" "stack-protector-buffer-size"="8" }
attributes #1 = { nounwind "frame-pointer"="all" "no-trapping-math"="true" "stack-protector-buffer-size"="8" }
attributes #2 = { nounwind }

!llvm.module.flags = !{!0, !1, !2, !3, !4}
!llvm.ident = !{!5}

!0 = !{i32 1, !"wchar_size", i32 4}
!1 = !{i32 8, !"PIC Level", i32 2}
!2 = !{i32 7, !"PIE Level", i32 2}
!3 = !{i32 7, !"uwtable", i32 2}
!4 = !{i32 7, !"frame-pointer", i32 2}
!5 = !{!"Ubuntu clang version 18.1.3 (1ubuntu1)"}
