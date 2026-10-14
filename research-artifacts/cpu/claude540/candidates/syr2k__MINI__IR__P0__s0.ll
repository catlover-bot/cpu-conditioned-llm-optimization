; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_syr2k(i32 noundef %n, i32 noundef %m, double noundef %alpha, double noundef %beta, ptr noundef %C, ptr noundef %A, ptr noundef %B) #0 {
entry:
  %cmp_n = icmp sgt i32 %n, 0
  br i1 %cmp_n, label %outer.preheader, label %for.end51

outer.preheader:
  %n64 = sext i32 %n to i64
  %m64 = sext i32 %m to i64
  %cmp_m = icmp sgt i32 %m, 0
  br label %for.cond

for.cond:                                         ; preds = %for.inc49, %outer.preheader
  %i = phi i32 [ 0, %outer.preheader ], [ %inc50, %for.inc49 ]
  %i64 = sext i32 %i to i64
  %crow_off = mul nsw i64 %i64, %n64
  %crow = getelementptr inbounds double, ptr %C, i64 %crow_off
  %jub1 = add nsw i32 %i, 1
  br label %for.body8.preheader

for.body8.preheader:
  br label %for.body8

for.body8:                                        ; preds = %for.body8.preheader, %for.body8
  %j1 = phi i32 [ 0, %for.body8.preheader ], [ %inc.j1, %for.body8 ]
  %j1_64 = sext i32 %j1 to i64
  %arrayidx10 = getelementptr inbounds double, ptr %crow, i64 %j1_64
  %v10 = load double, ptr %arrayidx10, align 8
  %mul = fmul double %v10, %beta
  store double %mul, ptr %arrayidx10, align 8
  %inc.j1 = add nsw i32 %j1, 1
  %cmp7 = icmp slt i32 %inc.j1, %jub1
  br i1 %cmp7, label %for.body8, label %for.end

for.end:                                          ; preds = %for.body8
  br i1 %cmp_m, label %for.body13.preheader, label %for.end48

for.body13.preheader:
  br label %for.cond11

for.cond11:                                       ; preds = %for.inc46, %for.body13.preheader
  %k = phi i32 [ 0, %for.body13.preheader ], [ %inc47, %for.inc46 ]
  %k64 = sext i32 %k to i64
  %arow_off = mul nsw i64 %i64, %m64
  %Aik_ptr = getelementptr inbounds double, ptr %A, i64 %arow_off
  %Aik_ptr2 = getelementptr inbounds double, ptr %Aik_ptr, i64 %k64
  %Aik = load double, ptr %Aik_ptr2, align 8
  %alpha_Aik = fmul double %Aik, %alpha

  %Bik_ptr = getelementptr inbounds double, ptr %B, i64 %arow_off
  %Bik_ptr2 = getelementptr inbounds double, ptr %Bik_ptr, i64 %k64
  %Bik = load double, ptr %Bik_ptr2, align 8

  %alpha_Bik = fmul double %Bik, %alpha

  br label %for.body16

for.body16:                                       ; preds = %for.cond11, %for.body16
  %j2 = phi i32 [ 0, %for.cond11 ], [ %inc.j2, %for.body16 ]
  %j2_64 = sext i32 %j2 to i64

  %ajk_row_off = mul nsw i64 %j2_64, %m64
  %Ajk_ptr = getelementptr inbounds double, ptr %A, i64 %ajk_row_off
  %Ajk_ptr2 = getelementptr inbounds double, ptr %Ajk_ptr, i64 %k64
  %Ajk = load double, ptr %Ajk_ptr2, align 8

  %Bjk_ptr = getelementptr inbounds double, ptr %B, i64 %ajk_row_off
  %Bjk_ptr2 = getelementptr inbounds double, ptr %Bjk_ptr, i64 %k64
  %Bjk = load double, ptr %Bjk_ptr2, align 8

  %mul26 = fmul double %alpha_Aik, %Bjk
  %mul31 = fmul double %alpha_Bik, %Ajk
  %add37 = fadd double %mul26, %mul31

  %arrayidx41 = getelementptr inbounds double, ptr %crow, i64 %j2_64
  %cval = load double, ptr %arrayidx41, align 8
  %add42 = fadd double %cval, %add37
  store double %add42, ptr %arrayidx41, align 8

  %inc.j2 = add nsw i32 %j2, 1
  %cmp15 = icmp slt i32 %inc.j2, %jub1
  br i1 %cmp15, label %for.body16, label %for.inc46

for.inc46:                                        ; preds = %for.body16
  %inc47 = add nsw i32 %k, 1
  %cmp12 = icmp slt i32 %inc47, %m
  br i1 %cmp12, label %for.cond11, label %for.end48

for.end48:                                        ; preds = %for.inc46, %for.end
  br label %for.inc49

for.inc49:                                        ; preds = %for.end48
  %inc50 = add nsw i32 %i, 1
  %cmp = icmp slt i32 %inc50, %n
  br i1 %cmp, label %for.cond, label %for.end51

for.end51:                                        ; preds = %for.inc49, %entry
  ret void
}

attributes #0 = { noinline nounwind uwtable "frame-pointer"="all" "min-legal-vector-width"="0" "no-trapping-math"="true" "stack-protector-buffer-size"="8" }

!llvm.module.flags = !{!0, !1, !2, !3, !4}
!llvm.ident = !{!5}

!0 = !{i32 1, !"wchar_size", i32 4}
!1 = !{i32 8, !"PIC Level", i32 2}
!2 = !{i32 7, !"PIE Level", i32 2}
!3 = !{i32 7, !"uwtable", i32 2}
!4 = !{i32 7, !"frame-pointer", i32 2}
!5 = !{!"Ubuntu clang version 18.1.3 (1ubuntu1)"}
