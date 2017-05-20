import { PlaceResult } from "./place-autocomplete";
import { URLSearchParams } from "@angular/http";

interface PickerDate {
    date: {
        day: number;
        month: number;
        year: number;
    };
    epoc: number;
    formatted: string;
    jsdate: Date;
}

export class Search {
    constructor(public startDate?: PickerDate,
                public endDate?: PickerDate,
                public driveHours?: number,
                public fromPlace?: PlaceResult) {
    }

    public toQuery(): URLSearchParams {
        let params = new URLSearchParams();
        params.set('start_date', this.startDate.formatted);
        params.set('end_date', this.endDate.formatted);
        params.set('drive_hours', '' + this.driveHours);
        params.set('from_place', this.fromPlace ? this.fromPlace.formatted_address : '');
        return params;
    }
}

export class FreePark {
    constructor(public parkName: string,
                public freeSites: number,
                public parentParkName?: string,
                public driveHours?: number) {
    }
}

export class CampSite {
    constructor(public parkName: string,
                public siteNumber: string,
                public campgroundName?: string,
                public parentParkName?: string,
                public details?: { [index: string]: string },
                public images?: { [index: number]: string }) {
    }
}
