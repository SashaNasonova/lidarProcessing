#query lasinfo reports by file for collection disagreements

indir="C:/Data/Woodlot_0007/laz_bcalb_reclass"

flist=list.files(indir, ".txt$", full.names=TRUE)
omat=as.data.frame(matrix(NA, nrow=length(flist), ncol=33))
names(omat)=c("filename","las_version","point_data_format","day","year","min_acquisition_date", "max_acquisition_date","global_encoding","geokey_HCRS","geokey_VCRS","wkt_CRS","n_points","n_points_withheld","sampled_area_square_meters","point_sampling_density_per_square_meter","point_sampling_spacing_meters","minx","maxx","miny","maxy","minz","maxz","min_no_return","max_no_return","min_return_no", "max_return_no", "min_class","max_class","unique_class", "min_int","max_int","min_scan", "max_scan")
omat$filename=flist
rm(flist)

for(i in 1:dim(omat)[1]){
	info=readLines(omat$filename[i])

	if(any(grepl("major.minor",info))){
		omat$las_version[i]=regmatches(info[grep("major.minor", info)], regexpr("[0-9]+.[0-9]+", info[grep("major.minor", info)]))
	}

	if(any(grepl("point data format",info))){
		omat$point_data_format[i]=regmatches(info[grep("point data format", info)], regexpr("[0-9]+", info[grep("point data format", info)]))
	}

	if(any(grepl("ProjectedCSTypeGeoKey: ",info))){
		omat$geokey_HCRS[i]=unlist(strsplit(info[grep("ProjectedCSTypeGeoKey", info)], "ProjectedCSTypeGeoKey: "))[2]
	}

	if(any(grepl("VerticalCSTypeGeoKey: ",info))){
		omat$geokey_VCRS[i]=unlist(strsplit(info[grep("VerticalCSTypeGeoKey", info)], "VerticalCSTypeGeoKey: "))[2]
	}

	if(any(grepl("WKT OGC COORDINATE SYSTEM:",info))){
		omat$wkt_CRS[i]=sub("^\\s+", "", info[grep("WKT OGC COORDINATE SYSTEM:", info)+1])
	}

	if(any(grepl("covered area in square meters/kilometers: ",info))){
		omat$sampled_area_square_meters[i]=unlist(strsplit(unlist(strsplit(info[grep("covered area in square meters/kilometers: ", info)], "covered area in square meters/kilometers: "))[2],"/"))[1]
	}

	if(any(grepl("point density: .* last only",info))){
		omat$point_sampling_density_per_square_meter[i]=unlist(strsplit(info[grep("point density: .* last only", info)], "\\s+"))[grep("\\d+", unlist(strsplit(info[grep("point density: .* last only", info)], "\\s+")))][2]
	}

	if(any(grepl("spacing: .* last only",info))){
		omat$point_sampling_spacing_meters[i]=unlist(strsplit(info[grep("spacing: .* last only", info)], "\\s+"))[grep("\\d+", unlist(strsplit(info[grep("spacing: .* last only", info)], "\\s+")))][2]
	}

	if(any(grepl("day/year",info))){
		omat$day[i]=sub("/$", "", regmatches(info[grep("day/year", info)], regexpr("[0-9]+/", info[grep("day/year", info)])))
		omat$year[i]=sub("^/", "", regmatches(info[grep("day/year", info)], regexpr("/[0-9]{4}", info[grep("day/year", info)])))
	}

	if (any(grepl("\\s+gps_time",info))){
		omat[i,c("min_acquisition_date","max_acquisition_date")]=as.character(as.Date("1980-01-06")+((as.numeric(tail(unlist(strsplit(info[grep("\\s+gps_time", info)], "\\s+")),2))+1000000000)/86400))
	}
	
	if(any(grepl("\\s+global_encoding", info))){
		omat$global_encoding[i]=as.numeric(sub("\\D+", "", info[grep("\\s+global_encoding",info)]))
	}	

	if(any(grepl("min x y z",info))){
		omat[i, c("minx","miny","minz")]=tail(unlist(strsplit(info[grep("min x y z", info)], "\\s+")),3)
	}
	if(any(grepl("max x y z",info))){
		omat[i, c("maxx","maxy","maxz")]=tail(unlist(strsplit(info[grep("max x y z", info)], "\\s+")),3)
	}
	if(any(grepl("intensity",info))){
		omat[i,c("min_int","max_int")]=tail(unlist(strsplit(info[grep("intensity", info)], "\\s+")),2)
	}
	if(any(grepl("^\\s+number_of_returns",info))){
		omat[i,c("min_no_return","max_no_return")]=tail(unlist(strsplit(info[grep("^\\s+number_of_returns", info)], "\\s+")),2)
	}
	if(any(grepl("^\\s+return_number",info))){
		omat[i,c("min_return_no","max_return_no")]=tail(unlist(strsplit(info[grep("^\\s+return_number", info)], "\\s+")),2)
	}
	if(any(grepl("^\\s+classification",info))){
		omat[i,c("min_class","max_class")]=tail(unlist(strsplit(info[grep("^\\s+classification", info)], "\\s+")),2)
	}	
	if(any(grepl("flagged as withheld:", info))){
		omat$n_points_withheld[i]=unlist(strsplit(info[grep("flagged as withheld:", info)],"\\D+"))[2]
		info=info[1: grep("flagged as withheld:", info)-1]
	}

	if(any(grepl("^histogram of classification",info))){
		temp=unlist(strsplit(info[(grep("^histogram of classification", info)+1):length(info)],"\\s+"))
		omat$n_points[i]=sum(as.numeric(temp[grep("^[0-9]+$", temp)]))
		omat[i,"unique_class"]=paste(gsub("\\W","", unlist(regmatches(info[(grep("^histogram of classification", info)+1):length(info)], gregexpr("\\W{1}\\d{1,3}\\W{1}$",info[(grep("^histogram of classification", info)+1):length(info)])))),collapse=" ")
	}

	if(any(grepl("scan_angle_rank",info))){
		omat[i,c("min_scan","max_scan")]=tail(unlist(strsplit(info[grep("scan_angle_rank", info)], "\\s+")),2)
	}
}

omat=as.data.frame(omat)
omat[,which(!names(omat) %in% c("filename","min_acquisition_date", "max_acquisition_date", "geokey_HCRS", "geokey_VCRS", "wkt_CRS", "unique_class"))]=sapply(omat[,which(!names(omat) %in% c("filename","min_acquisition_date", "max_acquisition_date", "geokey_HCRS", "geokey_VCRS", "wkt_CRS", "unique_class"))], as.numeric)
of=paste0(indir,"/las_info_table.csv")
#omat[which(omat$global_encoding==0), c("min_acquisition_date","max_acquisition_date")]=NA
omat[which(omat$global_encoding %in% c(0,16)), c("min_acquisition_date","max_acquisition_date")]=NA #update Aug 16
write.csv(omat, of, row.names=FALSE)

#flist=list.files(indir, full.names=TRUE)
#unlink(flist[grep(basename(of), basename(flist),invert=TRUE)])

of=sub("_table", "_summaryTable", of)

omat$las_version[which(!is.na(omat$las_version))]=paste0("V",omat$las_version[which(!is.na(omat$las_version))]) 
write.table(data.frame(rbind(c("Las Version"="tile count", table(omat$las_version))," ")), of, sep=",", row.names=FALSE, col.names=TRUE)

omat$point_data_format[which(!is.na(omat$point_data_format))]=paste0("Type",omat$point_data_format[which(!is.na(omat$point_data_format))])
suppressWarnings(
	write.table(data.frame(rbind(c("Point Data Type"="tile count", table(omat$point_data_format))," ")), of, sep=",", row.names=FALSE, col.names=TRUE, append=TRUE)
)

collect=unique(paste0(basename(omat$filename), omat$min_acquisition_date), paste0(basename(omat$filename),omat$max_acquisition_date))
collect=collect[grep("NA$", collect, invert=TRUE)]
collect=regmatches(collect, regexpr("[0-9]{4}-[0-9]{2}-[0-9]{2}", collect))
suppressWarnings(
	write.table(data.frame(rbind(c("Acquisition dates"="tile count", table(collect), "unresolved_GPS_week"=length(which(omat$global_encoding==0))), " ")), of, sep=",", row.names=FALSE, col.names=TRUE, append=TRUE)
)


omat$geokey_HCRS=gsub("[^A-z0-9]", "", omat$geokey_HCRS)
suppressWarnings(
	write.table(data.frame(rbind(c("Horizontal CRS"="tile count", table(omat$geokey_HCRS))," ")), of, sep=",", row.names=FALSE, col.names=TRUE, append=TRUE)
)

omat$geokey_VCRS=gsub("[^A-z0-9]", "", omat$geokey_VCRS)
suppressWarnings(
	write.table(data.frame(rbind(c("Vertical CRS"="tile count", table(omat$geokey_VCRS))," ")), of, sep=",", row.names=FALSE, col.names=TRUE, append=TRUE)
)

suppressWarnings(
	write.table(data.frame(rbind(c("Number of unique WKT CRS"=length(unique(omat$wkt_CRS)))," ")), of, sep=",", row.names=FALSE, col.names=TRUE, append=TRUE)
)

omat$unique_class=paste0("class_", gsub("\\s+", "_", omat$unique_class))
suppressWarnings(
	write.table(data.frame(rbind(c("unique point classes"="tile count", table(omat$unique_class))," ")), of, sep=",", row.names=FALSE, col.names=TRUE, append=TRUE)
)

classTab=data.frame(rbind(round(do.call(rbind,tapply(omat$maxz-omat$minz, omat$unique_class, FUN=function(x) summary(x))),2)," "))
classTab$class=row.names(classTab)
names(classTab)[-ncol(classTab)]=c("min", "q1", "q2", "mean", "q3", "max")
classTab[nrow(classTab),]=" "
classTab=cbind(z_range_by_class_set=classTab$class, classTab[,-ncol(classTab)])
suppressWarnings(
	write.table(data.frame(classTab), of, sep=",", row.names=FALSE, col.names=TRUE, append=TRUE)
)


temp=data.frame(rbind(c(summary_number_of_points=" ", summary(omat$n_points)), " "))
names(temp)[-1]=c("min", "q1", "q2", "mean", "q3", "max")
suppressWarnings(
	write.table(temp, of, sep=",", row.names=FALSE, col.names=TRUE, append=TRUE)
)

temp=data.frame(rbind(c(summary_number_of_points_withheld=" ", summary(omat$n_points_withheld)), " "))
if(any(grepl("na", names(temp), ignore.case=TRUE))){
	names(temp)[-1]=c("min", "q1", "q2", "mean", "q3", "max", "na_count")
}else{
	names(temp)[-1]=c("min", "q1", "q2", "mean", "q3", "max")
}
suppressWarnings(
	write.table(temp, of, sep=",", row.names=FALSE, col.names=TRUE, append=TRUE)
)

temp=data.frame(rbind(c(summary_of_tile_sampled_area_square_meters=" ", summary(omat$sampled_area_square_meters)), " "))
if(any(grepl("na", names(temp), ignore.case=TRUE))){
	names(temp)[-1]=c("min", "q1", "q2", "mean", "q3", "max", "na_count")
}else{
	names(temp)[-1]=c("min", "q1", "q2", "mean", "q3", "max")
}
suppressWarnings(
	write.table(temp, of, sep=",", row.names=FALSE, col.names=TRUE, append=TRUE)
)

temp=data.frame(rbind(c(summary_of_tile_sampling_density_by_square_meter=" ", summary(omat$point_sampling_density_per_square_meter)), " "))
names(temp)[-1]=c("min", "q1", "q2", "mean", "q3", "max")
suppressWarnings(
	write.table(temp, of, sep=",", row.names=FALSE, col.names=TRUE, append=TRUE)
)

temp=data.frame(rbind(c(summary_of_tile_sampling_spacing_in_meters=" ", summary(omat$point_sampling_spacing_meters)), " "))
names(temp)[-1]=c("min", "q1", "q2", "mean", "q3", "max")
suppressWarnings(
	write.table(temp, of, sep=",", row.names=FALSE, col.names=TRUE, append=TRUE)
)

temp=data.frame(rbind(c(summary_of_tile_max_number_of_returns=" ", summary(omat$max_no_return)), " "))
names(temp)[-1]=c("min", "q1", "q2", "mean", "q3", "max")
suppressWarnings(
	write.table(temp, of, sep=",", row.names=FALSE, col.names=TRUE, append=TRUE)
)

temp=data.frame(rbind(c(summary_of_tile_max_return_number=" ", summary(omat$max_return_no)), " "))
names(temp)[-1]=c("min", "q1", "q2", "mean", "q3", "max")
suppressWarnings(
	write.table(temp, of, sep=",", row.names=FALSE, col.names=TRUE, append=TRUE)
)

temp=data.frame(rbind(c(summary_of_tile_min_intensity=" ", summary(omat$min_int)), " "))
names(temp)[-1]=c("min", "q1", "q2", "mean", "q3", "max")
suppressWarnings(
	write.table(temp, of, sep=",", row.names=FALSE, col.names=TRUE, append=TRUE)
)

temp=data.frame(rbind(c(summary_of_tile_max_intensity=" ", summary(omat$max_int)), " "))
names(temp)[-1]=c("min", "q1", "q2", "mean", "q3", "max")
suppressWarnings(
	write.table(temp, of, sep=",", row.names=FALSE, col.names=TRUE, append=TRUE)
)

temp=data.frame(rbind(c(summary_of_tile_max_scan_angle_rank=" ", summary(omat$max_scan)), " "))
names(temp)[-1]=c("min", "q1", "q2", "mean", "q3", "max")
suppressWarnings(
	write.table(temp, of, sep=",", row.names=FALSE, col.names=TRUE, append=TRUE)
)

temp=data.frame(rbind(c(summary_of_tile_min_scan_angle_rank=" ", summary(omat$min_scan)), " "))
names(temp)[-1]=c("min", "q1", "q2", "mean", "q3", "max")
suppressWarnings(
	write.table(temp, of, sep=",", row.names=FALSE, col.names=TRUE, append=TRUE)
)
